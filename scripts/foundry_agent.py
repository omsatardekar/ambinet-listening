
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from azure.identity import AzureCliCredential
from agent_framework.foundry import FoundryAgent as AzureFoundryAgent


class FoundryAPIError(RuntimeError):
    pass


class FoundryAgent:
    """
    Connect to and invoke an existing Microsoft Foundry Prompt Agent.

    Authentication:
        Microsoft Entra ID through AzureCliCredential.

    Agent configuration:
        Managed in the Foundry portal, not created by this script.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str = "",
        model: str = "",
        agent_name: str = "clinical-conversation-reconstruction",
        api_version: str = "v1",
        timeout: int = 300,
        max_output_tokens: int = 24000,
        max_retries: int = 4,
        retry_base_seconds: float = 3.0,
        agent_version: str = "5",
    ):
        self.endpoint = endpoint.rstrip("/")
        self.agent_name = agent_name
        self.agent_version = str(agent_version)
        self.timeout = timeout

        # Retained for compatibility with the existing process_transcript.py.
        # Output-token limits must be configured in the Foundry agent/model
        # configuration; this value is not sent as an API-key REST parameter.
        self.max_output_tokens = max(24000, int(max_output_tokens))

        self.credential = AzureCliCredential()

        try:
            self.agent = AzureFoundryAgent(
                project_endpoint=self.endpoint,
                agent_name=self.agent_name,
                agent_version=self.agent_version,
                credential=self.credential,
                timeout=float(self.timeout),
            )
        except Exception:
            self.credential.close()
            raise

    def ensure_agent(
        self,
        instructions: str,
        force_update: bool = False,
    ) -> dict[str, Any]:
        """
        Reuse the existing agent.

        Agent creation and publishing are intentionally not performed here.
        Manage instructions and versions in the Foundry portal.
        """

        if force_update:
            raise FoundryAPIError(
                "Cannot publish agent versions from this script. "
                "Update and publish the agent in the Foundry portal."
            )

        print("Connected to existing Foundry agent configuration:")
        print(f"  Agent name    : {self.agent_name}")
        print(f"  Agent version : {self.agent_version}")
        print("  Authentication: Microsoft Entra ID")

        return {
            "name": self.agent_name,
            "version": self.agent_version,
        }

    @staticmethod
    def _remove_json_fence(text: str) -> str:
        """Remove Markdown JSON fences if the agent accidentally adds them."""

        cleaned = text.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        return cleaned

    async def _run_agent(self, prompt: str) -> str:
        """Invoke the saved Foundry agent asynchronously."""

        response = await self.agent.run(prompt)

        # Agent Framework returns an AgentResponse object.
        # The generated response text is available through .text.
        output = response.text

        if not isinstance(output, str):
            raise FoundryAPIError(
                "Foundry agent returned an unexpected response type: "
                f"{type(output).__name__}"
            )

        return output.strip()

    def _run_agent_sync(self, prompt: str) -> str:
        """
        Synchronous wrapper for the current process_transcript.py CLI.

        Do not call this wrapper from an already-running async event loop.
        """

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_agent(prompt))

        raise FoundryAPIError(
            "A Python event loop is already running. "
            "For an async FastAPI endpoint, call "
            "'await agent._run_agent(prompt)' instead of reconstruct()."
        )

    def reconstruct(
        self,
        encounter_payload: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any]:
        """
        Reconstruct a clinical encounter using the existing Foundry agent.

        Python restores timestamps and original Azure speaker IDs from
        source segments in the subsequent validation stage.
        """

        compact_output_rules = """
IMPORTANT OUTPUT EFFICIENCY RULES:

Return one complete, valid JSON object only.

The input contains the complete encounter. Read and reason over the
complete encounter before deciding speaker identity or role.

The reconstruction_instructions in this request are the current
authoritative rules. Follow them if they differ from older instructions
on the saved agent.

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
- DEFAULT FOR A TWO-PERSON CONSULTATION: when the encounter has one PATIENT and exactly one other
  clinical participant who takes the history, evaluates the symptoms, explains clinical terms or
  considerations, and sets out a plan, assign DOCTOR with attribution_status PROVISIONAL and
  review_required true. A missing self-introduction or title is NOT a reason to use
  OTHER_CLINICAL_STAFF; put "no explicit title stated" in conflicting_evidence instead. This default
  does not apply when there is a nurse-type pattern (triage, recording vital signs, giving
  medication), an identifiable allied role (therapist, paramedic, technician, trainee), or a
  second clinician.
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
            compact_output_rules += _NORMALIZATION_RULES_V2

        user_payload = {
            "task": task,
            "output_rules": compact_output_rules,
            "reconstruction_instructions": instructions,
            "encounter": encounter_payload,
        }

        prompt = json.dumps(
            user_payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        print(
            "  Calling Foundry agent "
            f"{self.agent_name} (version {self.agent_version})..."
        )
        print(
            f"  Encounter segments: "
            f"{len(encounter_payload.get('segments', []))}"
        )

        try:
            output_text = self._run_agent_sync(prompt)

        except FoundryAPIError:
            raise

        except Exception as exc:
            raise FoundryAPIError(
                f"Foundry agent invocation failed: {exc}"
            ) from exc

        if not output_text:
            raise FoundryAPIError(
                "Foundry agent returned an empty response."
            )

        output_text = self._remove_json_fence(output_text)

        try:
            result = json.loads(output_text)

        except json.JSONDecodeError as exc:
            raise FoundryAPIError(
                "Agent returned incomplete or invalid JSON.\n"
                f"JSON error: {exc}\n"
                f"Output characters: {len(output_text)}\n"
                f"Output ending: {output_text[-700:]}"
            ) from exc

        if not isinstance(result, dict):
            raise FoundryAPIError(
                "Agent output JSON must be an object."
            )

        # Keep the fields expected by the downstream validation code.
        result["foundry_response_id"] = None
        result["model_deployment"] = (
            "Configured in Foundry agent: " + self.agent_name
        )

        return result

    def close(self) -> None:
        """Close the synchronous Azure CLI credential."""

        self.credential.close()


PROMPT_V2_MARKER = "prompt-version: 2"


_NORMALIZATION_RULES_V2 = """
TEXT NORMALIZATION (v2, applies only to the text field; segmentation
and speakers are unchanged):

- Convert dictated notation without changing any value:
  "slash" -> "/" (packet slash notes -> packet/notes),
  "one twenty over eighty" -> "120/80",
  "ninety eight point six" -> "98.6",
  "five milligrams" -> "5 mg",
  "percent" -> "%".

- Write measurements, vitals, doses, durations and counts as digits;
  keep idiomatic words ("one thing", "one-sided").

- Never add words, units or certainty that were not spoken,
  and never change a number.
"""


def _same_text(left: str, right: str) -> bool:
    def normalize(value: str) -> str:
        return "\n".join(
            line.rstrip()
            for line in value.replace("\r\n", "\n").strip().split("\n")
        )

    return normalize(left) == normalize(right)


def load_instructions(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
