"""Token-count study of transcript renderings on the 50 prompt-development INPUT transcripts only (no labels, validation or locked-test files).
R0 = existing renderer line; R1 = 'role: text' with no ids or times; R2 = 'Sn role: text' (short line number kept so facts can be traced; mapping sidecar below).
Also builds the segment mapping sidecar for the R1/R2 design and checks that role labels are unambiguous (one speaker per role).
usage: python -B render_token_study.py"""
import json
import statistics as st
from pathlib import Path

import openvino_genai as ovg

HERE = Path(__file__).resolve().parent
EXP7 = HERE.parent
ROOT = EXP7.parents[2]
ids = json.loads((EXP7.parent / "EXP_006_S1_SIMPLIFIED_EXTRACTION" / "config" / "S1_CONFIG.json").read_text(encoding="utf-8"))["ids"]
tok = ovg.Tokenizer(str(EXP7.parent / "EXP_002_QWEN3_0.6B_GPU_DIRECT" / "models" / "Qwen3-0.6B-ov-fp16"))


def n(text):
    return int(tok.encode(text).input_ids.shape[1])


rows, sidecar_example, ambiguous, unknown_roles = [], None, 0, 0
for i in ids:
    d = json.loads((ROOT / "dataset_v2_batch_001_corrected" / "output" / "inputs" / f"encounter_{i}.json").read_text(encoding="utf-8"))
    segs = d["segments"]
    r0 = "\n".join(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}) {s['start_seconds']:.2f}-{s['end_seconds']:.2f}s: {s['text']}" for s in segs)
    r1 = "\n".join(f"{s['role'].lower()}: {s['text']}" for s in segs)
    r2 = "\n".join(f"S{k + 1} {s['role'].lower()}: {s['text']}" for k, s in enumerate(segs))
    rows.append((n(r0), n(r1), n(r2)))
    per = {}
    for s in segs:
        per.setdefault(s["role"], set()).add(s["speaker_id"])
    ambiguous += any(len(v) > 1 for v in per.values())
    unknown_roles += sum(1 for s in segs if s["role"] == "UNKNOWN")
    if sidecar_example is None:
        sidecar_example = {"encounter_id": i, "rendering": "R2", "lines": [{"label": f"S{k + 1}", "segment_id": s["segment_id"], "speaker_id": s["speaker_id"], "role": s["role"],
                                                                         "start_seconds": s["start_seconds"], "end_seconds": s["end_seconds"]} for k, s in enumerate(segs[:3])], "note": "first 3 of N lines shown"}
res = {"records": len(ids), "transcript_tokens_mean": {"R0_current": round(st.mean(r[0] for r in rows), 1), "R1_role_label_only": round(st.mean(r[1] for r in rows), 1),
                                                   "R2_line_number_plus_role": round(st.mean(r[2] for r in rows), 1)},
       "saving_vs_R0_mean_tokens": {"R1": round(st.mean(r[0] - r[1] for r in rows), 1), "R2": round(st.mean(r[0] - r[2] for r in rows), 1)},
       "saving_vs_R0_percent_of_transcript": {"R1": round(100 * (1 - sum(r[1] for r in rows) / sum(r[0] for r in rows)), 1), "R2": round(100 * (1 - sum(r[2] for r in rows) / sum(r[0] for r in rows)), 1)},
       "records_where_two_speakers_share_a_role": ambiguous, "UNKNOWN_role_segments": unknown_roles, "sidecar_example": sidecar_example}
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results" / "render_token_study.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
