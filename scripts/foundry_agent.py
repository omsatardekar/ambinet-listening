
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


class FoundryAPIError(RuntimeError):
    pass


class FoundryAgent:
    """Create/reuse and invoke a Microsoft Foundry prompt agent."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        agent_name: str,
        api_version: str = "v1",
        timeout: int = 300,
        max_output_tokens: int = 24000,
        max_retries: int = 4,
        retry_base_seconds: float = 3.0,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.agent_name = agent_name
        self.api_version = api_version
        self.timeout = timeout

        # A larger output budget helps prevent incomplete JSON responses.
        # The minimum is enforced even if the old .env still says 12000.
        self.max_output_tokens = max(24000, int(max_output_tokens))

        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds

        self.session = requests.Session()
        self.session.headers.update({
            "api-key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "clinical-transcript-reconstruction/1.1",
        })

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs,
                )

                if response.status_code not in (429, 500, 502, 503, 504):
                    return response

                last_error = FoundryAPIError(
                    f"Foundry returned HTTP {response.status_code}: "
                    f"{response.text[:1500]}"
                )

                if attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")

                    if retry_after and retry_after.isdigit():
                        delay = float(retry_after)
                    else:
                        delay = self.retry_base_seconds * (2 ** attempt)

                    time.sleep(min(delay, 60))

            except requests.RequestException as exc:
                last_error = exc

                if attempt < self.max_retries:
                    time.sleep(
                        min(self.retry_base_seconds * (2 ** attempt), 60)
                    )

        raise FoundryAPIError(str(last_error))

    def ensure_agent(
        self,
        instructions: str,
        force_update: bool = False,
    ) -> dict[str, Any]:

        agent_url = (
            f"{self.endpoint}/agents/{self.agent_name}"
            f"?api-version={self.api_version}"
        )

        existing = self._request("GET", agent_url)

        if existing.status_code == 200:
            # Publish a new agent version automatically when the instruction file
            # changed since the saved latest version (for example v1 -> v2).
            saved = None
            try:
                latest = (existing.json().get("versions") or {}).get("latest") or {}
                saved = (latest.get("definition") or {}).get("instructions")
            except (ValueError, AttributeError):
                saved = None
            if isinstance(saved, str) and _same_text(saved, instructions) is False:
                force_update = True
                print("Agent instructions changed; creating a new agent version.")

            if force_update:
                version_url = (
                    f"{self.endpoint}/agents/{self.agent_name}/versions"
                    f"?api-version={self.api_version}"
                )
                payload = {
                    "definition": {
                        "kind": "prompt",
                        "model": self.model,
                        "instructions": instructions,
                    },
                }
                response = self._request(
                    "POST",
                    version_url,
                    json=payload,
                )
                self._raise_for_status(response, "Create Foundry agent version")
                body = response.json()
                print(f"Created new Foundry agent version: {self.agent_name}")
                if body.get("version"):
                    print(f"Agent version: {body['version']}")
                return body

            body = existing.json()
            print(
                "Foundry agent already exists; reusing: "
                f"{self.agent_name}"
            )
            return body

        if existing.status_code not in (404, 405):
            self._raise_for_status(
                existing,
                "Check existing agent",
            )

        create_url = (
            f"{self.endpoint}/agents"
            f"?api-version={self.api_version}"
        )

        payload = {
            "name": self.agent_name,
            "definition": {
                "kind": "prompt",
                "model": self.model,
                "instructions": instructions,
            },
        }

        response = self._request(
            "POST",
            create_url,
            json=payload,
        )

        self._raise_for_status(response, "Create Foundry agent")

        body = response.json()

        print(f"Created Foundry agent: {self.agent_name}")

        if body.get("id"):
            print(f"Agent ID: {body['id']}")

        if body.get("version"):
            print(f"Agent version: {body['version']}")

        return body

    @staticmethod
    def _raise_for_status(
        response: requests.Response,
        operation: str,
    ) -> None:

        if response.ok:
            return

        request_id = response.headers.get(
            "x-request-id",
            "not supplied",
        )

        client_request_id = response.headers.get(
            "x-ms-client-request-id",
            "not supplied",
        )

        raise FoundryAPIError(
            f"{operation} failed: HTTP {response.status_code}; "
            f"x-request-id={request_id}; "
            f"x-ms-client-request-id={client_request_id}; "
            f"response={response.text[:2500]}"
        )

    @staticmethod
    def _extract_output_text(body: dict[str, Any]) -> str:
        """Extract generated text from the Responses API response."""

        output_text = body.get("output_text")

        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        chunks = []

        for item in body.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if (
                    content.get("type") in ("output_text", "text")
                    and isinstance(content.get("text"), str)
                ):
                    chunks.append(content["text"])

        return "\n".join(chunks).strip()

    @staticmethod
    def _remove_json_fence(text: str) -> str:
        """Remove Markdown fences if the model accidentally adds them."""

        cleaned = text.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        return cleaned

    def reconstruct(
        self,
        encounter_payload: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any]:
        """
        Invoke the saved Foundry agent.

        The model returns compact reconstruction decisions.
        Python restores timestamps and original Azure IDs from
        the source transcript, avoiding unnecessary repeated output.
        """

        url = f"{self.endpoint}/openai/v1/responses"

        compact_output_rules = """
IMPORTANT OUTPUT EFFICIENCY RULES:

Return one complete, valid JSON object only.

The input contains the complete encounter. Read and reason over the
complete encounter before deciding speaker identity or role.

The reconstruction_instructions in this request are the current authoritative
rules. Follow them if they differ from older instructions on the saved agent.

Do not repeat information that Python can derive from source segments.

For each speaker_registry item, return only:
- canonical_speaker_id
- role
- role_confidence
- attribution_status
- original_azure_speaker_ids
- evidence
- conflicting_evidence
- review_required

Keep evidence and conflicting_evidence concise:
maximum 2 short items in each array.

For each utterance, return only:
- utterance_id
- canonical_speaker_id
- role
- text
- source_segment_indices
- attribution_confidence
- attribution_status
- reconstruction_type
- notes

Do NOT return start_seconds, end_seconds, duration_seconds,
or original_azure_speaker_ids for utterances. Python will derive
these fields from the original source segments.

Keep notes empty unless a specific review explanation is necessary.
Do not repeat the same evidence in every utterance.

Every input source segment index must be represented.
Do not omit any source text.
Do not invent source indices.

PRESERVE SOURCE TURNS:
- Default to one output utterance per input source segment.
- Never merge source segments with different non-empty speaker_id values.
- Never merge a question and its response, a handoff, a correction, or two
  distinct conversational turns, even when they discuss the same subject.
- Merge fragments only when one uninterrupted speaker turn is strongly
  supported. If uncertain, keep segments separate and mark attribution for review.
- Do not infer extra participants or roles merely because diarization has few IDs
  or because a clinic is expected to have a doctor and nurse.

Distinguish participant roles independently:
- Use DOCTOR only when explicit identity or the full context supports a physician role.
- Use NURSE only when explicit identity or the full context supports a nursing role.
- Use OTHER_CLINICAL_STAFF only when a clinical role is clear but a more specific role is not.
- Do not use clinical-staff as a substitute for DOCTOR or NURSE when the evidence supports either.
- Asking questions, reading observations, or being present in a clinic is not enough by itself to distinguish these roles.
- If the text does not support a reliable distinction, use UNKNOWN or PROVISIONAL and identify the uncertainty.

COARSE OR UNCERTAIN DIARIZATION:
- A low source speaker count may mean diarization is coarse, but does not prove that
  hidden participants exist.
- Preserve conversational turns and source boundaries. Do not invent speakers or roles.
- Assign UNKNOWN/PROVISIONAL and NEEDS_REVIEW when text cannot reliably distinguish identity.

The response must be complete JSON. Never stop in the middle
of an object or string. If uncertain, use UNKNOWN and NEEDS_REVIEW
rather than writing lengthy explanations.
"""

        task = (
            "Conservatively reconstruct this complete clinical encounter. "
            "Preserve source turns and boundaries, assign speakers and roles "
            "only where supported, and return the required compact JSON."
        )
        if PROMPT_V2_MARKER in instructions:
            compact_output_rules = compact_output_rules.replace(
                _PRESERVE_TURNS_V1, _PRESERVE_TURNS_V2
            )
            task = (
                "Reconstruct this complete clinical encounter. Decide the speaker of "
                "every segment first, then combine directly consecutive segments of "
                "the same speaker into one utterance, repair stray fragments, convert "
                "dictated symbols and numbers to clinical notation without changing "
                "values, never merge different speakers, and return the required "
                "compact JSON."
            )

        user_payload = {
            "task": task,
            "output_rules": compact_output_rules,
            "reconstruction_instructions": instructions,
            "encounter": encounter_payload,
        }

        request_body = {
            "model": self.model,
            "agent_reference": {
                "type": "agent_reference",
                "name": self.agent_name,
            },
            "input": json.dumps(
                user_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "max_output_tokens": self.max_output_tokens,
            "store": False,
        }

        print(
            "  Calling Foundry agent "
            f"(output budget: {self.max_output_tokens} tokens)..."
        )

        response = self._request(
            "POST",
            url,
            json=request_body,
        )

        self._raise_for_status(
            response,
            "Invoke Foundry agent",
        )

        body = response.json()
        output_text = self._extract_output_text(body)

        if not output_text:
            raise FoundryAPIError(
                "Foundry response contained no output text. "
                f"Response ID: {body.get('id', 'unknown')}; "
                f"status: {body.get('status', 'unknown')}; "
                f"incomplete_details: "
                f"{body.get('incomplete_details')}"
            )

        output_text = self._remove_json_fence(output_text)

        try:
            result = json.loads(output_text)

        except json.JSONDecodeError as exc:
            status = body.get("status", "unknown")
            incomplete_details = body.get("incomplete_details")
            usage = body.get("usage")

            tail = output_text[-700:]

            raise FoundryAPIError(
                "Agent returned incomplete or invalid JSON.\n"
                f"JSON error: {exc}\n"
                f"Response status: {status}\n"
                f"Incomplete details: {incomplete_details}\n"
                f"Output characters: {len(output_text)}\n"
                f"Output token usage: {usage}\n"
                f"Output ending: {tail}"
            ) from exc

        if not isinstance(result, dict):
            raise FoundryAPIError(
                "Agent output JSON must be an object."
            )

        result["foundry_response_id"] = body.get("id")
        result["model_deployment"] = body.get("model", self.model)

        return result


PROMPT_V2_MARKER = "prompt-version: 2"


def _same_text(left: str, right: str) -> bool:
    def normalize(value: str) -> str:
        return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").strip().split("\n"))

    return normalize(left) == normalize(right)

_PRESERVE_TURNS_V1 = """PRESERVE SOURCE TURNS:
- Default to one output utterance per input source segment.
- Never merge source segments with different non-empty speaker_id values.
- Never merge a question and its response, a handoff, a correction, or two
  distinct conversational turns, even when they discuss the same subject.
- Merge fragments only when one uninterrupted speaker turn is strongly
  supported. If uncertain, keep segments separate and mark attribution for review.
- Do not infer extra participants or roles merely because diarization has few IDs
  or because a clinic is expected to have a doctor and nurse."""

_PRESERVE_TURNS_V2 = """SPEAKER TURNS (v2 rules, these replace any earlier one-utterance-per-segment default):
- First decide the speaker of every source segment from the whole conversation.
- Directly consecutive segments of the SAME speaker become ONE utterance. List every
  merged index in source_segment_indices (ascending, contiguous) and use
  reconstruction_type MERGED_FRAGMENTS. Keep all of their text, cleaned and joined.
- A stray one-to-three-word fragment (for example "We.") is attached to the
  neighbouring segment it continues, using that segment's speaker even when the
  fragment's source speaker_id differs. Repair the punctuation.
- Never merge different speakers: questions and answers, handoffs, interpreter
  relays, corrections, interruptions and backchannels from another speaker stay
  separate utterances. Never merge across another speaker's segment.
- Convert dictated symbols and spoken numbers to clinical notation without changing
  any value ("slash" -> "/", "one twenty over eighty" -> "120/80", "ninety eight
  point six" -> "98.6"). Do not add words, units or certainty that were not said.
- Do not infer extra participants or roles merely because diarization has few IDs
  or because a clinic is expected to have a doctor and nurse."""


def load_instructions(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
