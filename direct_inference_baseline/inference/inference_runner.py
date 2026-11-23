"""Direct inference runner. Reads TRANSCRIPT files only (never labels), calls the selected provider, and stores
raw responses, parsed predictions and failures separately. Failed outputs are never replaced by empty JSON."""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import time
from datetime import datetime, timezone

from ..config import settings as S
from ..evaluation import schema_validator as SV
from .base_client import BaseClient, PermanentInferenceError, TransientInferenceError
from .output_parser import parse_response

log = logging.getLogger("direct_inference")


def load_prompt_template() -> str:
    return S.PROMPT_PATH.read_text(encoding="utf-8")


def render_transcript(inp: dict) -> str:
    """Module-2 transcript -> text. Uses ONLY segment_id, speaker_id, role, times and text from the transcript file."""
    lines = []
    for s in inp["segments"]:
        lines.append(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}) {s['start_seconds']:.2f}-{s['end_seconds']:.2f}s: {s['text']}")
    return "\n".join(lines)


def load_transcript(eid: str) -> dict:
    p = S.INPUT_DIR / f"encounter_{eid}.json"
    assert p.parent.resolve() == S.INPUT_DIR.resolve(), "transcripts are read only from the frozen inputs directory"
    return json.loads(p.read_text(encoding="utf-8"))


def build_prompt(eid: str, inp: dict | None = None, template: str | None = None) -> str:
    inp = inp or load_transcript(eid)
    t = template or load_prompt_template()
    return t.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", render_transcript(inp))


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=S.PROJECT_ROOT, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except Exception:
        return None


def new_experiment_id(provider: str, split: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"exp_{provider}_{split}_{ts}"


def run_inference(client: BaseClient, ids: list[str], split: str, max_new_tokens: int, experiment_id: str | None = None,
                  resume: bool = True, retries: int = 3, base_seconds: float = 2.0, sleep=time.sleep) -> dict:
    exp = experiment_id or new_experiment_id(client.provider, split)
    raw_d, parsed_d, failed_d, rep_d = (d / exp for d in (S.RAW_DIR, S.PARSED_DIR, S.FAILED_DIR, S.REPORT_DIR))
    for d in (raw_d, parsed_d, failed_d, rep_d):
        d.mkdir(parents=True, exist_ok=True)
    template = load_prompt_template()
    frozen = S.verify_frozen_dataset(inputs_only=True)
    if not frozen["verified"]:
        raise RuntimeError(f"frozen dataset does not match its checksums: {frozen['mismatches'][:3]}")
    manifest_path = rep_d / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "experiment_id": exp, "stage": "3 - direct inference baseline (no fine-tuning, no prompt optimisation, no RAG)",
        "started_utc": datetime.now(timezone.utc).isoformat(), "split": split, "encounter_ids": ids,
        "dataset": {"name": "dataset_v2_batch_001_corrected", "manifest_sha256": frozen["dataset_manifest_sha256"],
                    "frozen_files_verified": frozen["files_checked"]},
        "split_seed": json.loads((S.SPLIT_DIR / "split_metadata.json").read_text(encoding="utf-8")).get("seed") if (S.SPLIT_DIR / "split_metadata.json").exists() else None,
        "model": client.describe(), "max_new_tokens": max_new_tokens, "retry_policy": {"retries": retries, "base_seconds": base_seconds, "scope": "transient API/OOM errors only"},
        "prompt_file": "prompts/direct_extraction_prompt.txt", "prompt_sha256": hashlib.sha256(template.encode("utf-8")).hexdigest(),
        "prompt_text": template, "git_commit": git_commit(), "records": {}}
    for eid in ids:
        rawp = raw_d / f"encounter_{eid}.json"
        if resume and rawp.exists() and eid in manifest["records"]:
            continue
        rec = {"encounter_id": eid}
        try:
            inp = load_transcript(eid)
            prompt = build_prompt(eid, inp, template)
            res = client.generate(prompt, max_new_tokens, retries=retries, base_seconds=base_seconds, sleep=sleep)
            rawp.write_text(json.dumps({"encounter_id": eid, "response_text": res.text, "generation": res.as_dict()}, ensure_ascii=False, indent=1), encoding="utf-8")
            pr = parse_response(res.text, res.finish_reason)
            rec.update(finish_reason=res.finish_reason, prompt_tokens=res.prompt_tokens, completion_tokens=res.completion_tokens,
                       latency_seconds=round(res.latency_seconds, 3), attempts=res.attempts, parse_status=pr.status, parse_notes=pr.notes)
            if pr.status == "ok":
                sr = SV.validate(pr.data)
                (parsed_d / f"encounter_{eid}.json").write_text(json.dumps(pr.data, ensure_ascii=False, indent=1), encoding="utf-8")
                rec.update(status="parsed", schema_compliant=sr.compliant, schema_violation_counts=sr.counts,
                           schema_violations_sample=sr.violations[:15], keys_expected=sr.keys_expected, keys_present=sr.keys_present,
                           keys_emitted=sr.keys_emitted, keys_unexpected=sr.keys_unexpected)
            else:
                rec.update(status="failed", failure_type=pr.status)
                (failed_d / f"encounter_{eid}.json").write_text(json.dumps({"encounter_id": eid, "failure_type": pr.status, "notes": pr.notes,
                                                                            "finish_reason": res.finish_reason}, indent=1), encoding="utf-8")
        except (TransientInferenceError, PermanentInferenceError, Exception) as e:      # noqa: BLE001 - recorded, never swallowed
            rec.update(status="failed", failure_type="inference_error", error=f"{type(e).__name__}: {str(e)[:300]}")
            (failed_d / f"encounter_{eid}.json").write_text(json.dumps({"encounter_id": eid, "failure_type": "inference_error", "error": rec["error"]}, indent=1), encoding="utf-8")
        manifest["records"][eid] = rec
        manifest["last_update_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
        log.info("%s %s %s tok=%s %.1fs", eid, rec.get("status"), rec.get("parse_status", rec.get("failure_type")), rec.get("completion_tokens"), rec.get("latency_seconds", 0))
    return manifest
