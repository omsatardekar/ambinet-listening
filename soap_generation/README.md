# soap_generation: Module 4, the SOAP note (last step of the pipeline)

Additive module. It does not change transcription, reconstruction or extraction. One line in `backend/app/main.py` registers its routes; one line in `frontend/src/App.tsx` mounts its panel.

```
extraction-output / {NN}extraction.json ──► prepare (clean items, attach conversation passages, rule flags)
                                           ──► writer: Foundry prompt agent (default once created) or a deployed model
                                           ──► checks: format, then every number / medicine / allergy traced to the conversation
                                           ──► soap-output / {NN}soap.json + {NN}soap.md        ──► frontend "SOAP note" panel  (/api/soap/*)
```

## What it does
* **Input:** the saved extraction (`extraction_data` jobs are not used). Each finding gets a `ref`; the conversation passages linked to it travel with it, so the writer can check the finding against what was actually said.
* **Prompt:** `prompts/soap_agent_instructions_v1.md` (US outpatient SOAP: CC, HPI with OLDCARTS, ROS, PMH/PSH/FH/SH, medications, allergies; vitals, exam; numbered problem list with suggested ICD-10-CM; plan by problem; return precautions; clinician review block). Its rules are written against the mistakes the 0.6B extraction really makes (see `docs/MODULE3_FINETUNING_FOCUS.md`): invented allergies, copied doses, a price as a vital sign, a diagnosis nobody stated, a follow-up nobody arranged.
* **Safeguards in code (`prepare.py`, `guard.py`, `schema.py`):** rule flags for those mistakes are given to the writer; the answer must be valid JSON in one exact shape (one automatic retry); numbers, medicines and allergies of the finished note that cannot be found in the conversation are listed under "Before you sign". The note is never silently changed.
* **Output:** `{NN}soap.json` (note, review, markdown, generation info) and `{NN}soap.md` in the container `AZURE_STORAGE_SOAP_CONTAINER` (default `soap-output`, created automatically).

## Run it
```
python scripts/generate_soap.py --extraction path\51extraction.json --dry-run      # what would be sent: findings, flags (no model call)
python scripts/generate_soap.py --encounter 52 [--save]                            # from the extraction container; --save also uploads to soap-output
python scripts/generate_soap.py --extraction x.json --transcript compact.json      # also give the writer the whole conversation
```
In the app: **SOAP note > Generate SOAP note** under the clinical summary (the summary must have been generated first for that recording).

## Settings (`.env.example`)
| name | meaning |
|---|---|
| `AZURE_STORAGE_SOAP_CONTAINER` | container for finished notes (default `soap-output`) |
| `SOAP_BACKEND` | `agent` or `model`; empty = agent when `SOAP_AGENT_NAME` is set, else model |
| `SOAP_AGENT_NAME` / `SOAP_AGENT_VERSION` | the Foundry prompt agent; **the version is required** (written by `create_soap_agent.py --update-env`) |
| `SOAP_MODEL_ENDPOINT_URL` / `_API_KEY` / `_DEPLOYMENT` | direct model call; each falls back to the `JUDGE_*` setting |
| `SOAP_INCLUDE_TRANSCRIPT` | `0` (default, by design) = the writer works only from the extraction stage output; `1` = also give it the whole conversation (experiments only: it lets the writer override the extraction) |
| `SOAP_SEND_INSTRUCTIONS` | `0` (default) = the agent's stored prompt is used and requests stay short; `1` = also send the prompt with every request (only needed if you want the repository file to win over an older agent version) |

## Switching to the agent
1. `python scripts/create_soap_agent.py --dry-run` shows what would be created; `python scripts/create_soap_agent.py --model <deployment> --update-env` creates the agent version (needs `az login` and rights on the Foundry project). Or paste the instructions file into the portal (Agents > New agent).
2. In `.env`: `SOAP_BACKEND=agent`, `SOAP_AGENT_NAME=clinical-soap-note` and `SOAP_AGENT_VERSION=<version>` (`--update-env` writes the version for you). Restart the backend.
3. Changing the prompt later: edit `prompts/soap_agent_instructions_v1.md`, run `python scripts/create_soap_agent.py --model <deployment> --update-env` once (a new agent version), restart the backend.
4. Replacing the extraction model later (the fine-tuned one) changes nothing here: the module only reads the saved extraction.

## Tests
`python -m pytest soap_generation/tests -q` (no Azure, no model): input preparation and rule flags, parsing/normalising, traceability guard, rendering, a repair retry, the job service with fakes, the API.

## Limits
* By design the note follows the extraction: it can only contain what the extraction stage output (the findings and the conversation excerpts linked to them) holds, so an incomplete extraction gives an incomplete note (a thin or blank Plan, statements such as "not documented" that mean "not in the extraction"). The fine-tuned extraction model is what fixes this. `SOAP_INCLUDE_TRANSCRIPT=1` would let the writer override the extraction with the conversation and is meant for experiments only.
* ICD-10-CM codes are suggestions for the coder. All content is a draft for clinician review.
* Use synthetic data until real data is approved: the extraction goes to the agent or model you configured.
