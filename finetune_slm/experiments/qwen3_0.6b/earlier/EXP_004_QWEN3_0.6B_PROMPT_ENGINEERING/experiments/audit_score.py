"""Score the returned human-audit CSVs (no labels, no model). usage: audit_score.py <audit_dir>   (expects audit_key.json, phase1_responses.csv, phase2_responses.csv in the directory)
Reports every quantity separately; 45 facts is a feasibility check, not a statistically representative study. The retrieval rules must NOT be tuned on these results."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

d = Path(sys.argv[1])
key = {r["fact_id"]: r for r in json.loads((d / "audit_key.json").read_text(encoding="utf-8"))["items"]}
rd = lambda n: {r["fact_id"]: r for r in csv.DictReader(open(d / n, newline="", encoding="utf-8"))}
p1, p2 = rd("phase1_responses.csv"), rd("phase2_responses.csv")
c = Counter(); res = {}
for fid, k in key.items():
    a, b = p1.get(fid, {}), p2.get(fid, {})
    yes = lambda x: str(x).strip().lower() == "yes"
    c["facts"] += 1
    c[f"p1_supported_{(a.get('supported') or 'blank').lower()}"] += 1
    if k["decision"] == "cited":
        c["cited"] += 1
        c["cited_phase2_supports_yes"] += yes(b.get("supports")); c["cited_phase2_supports_partly"] += str(b.get("supports")).lower() == "partly"
        c["cited_relevant_yes"] += yes(b.get("relevant")); c["cited_speaker_ok"] += yes(b.get("speaker_ok")); c["cited_polarity_ok"] += yes(b.get("polarity_ok"))
        c["cited_context_ok"] += yes(b.get("context_ok")); c["cited_family_attr_ok"] += yes(b.get("family_attribution_ok"))
        sel = {s.strip() for s in str(a.get("supporting_segments") or "").replace(";", ",").split(",") if s.strip()}
        c["cited_reviewer_segments_overlap_system"] += bool(sel & set(k["segments"]))
        c["cited_phase1_fact_supported_yes"] += str(a.get("supported")).lower() == "yes"
    else:
        c["abstained"] += 1
        c["abstained_justified_yes"] += yes(b.get("abstention_justified"))
        c["abstained_reviewer_found_evidence_phase1"] += bool(str(a.get("supporting_segments") or "").strip())
        c["abstained_fact_supported_yes_phase1"] += str(a.get("supported")).lower() == "yes"
n_c, n_a = max(1, c["cited"]), max(1, c["abstained"])
res = {"counts": dict(c), "cited": {"supports_yes_rate": round(c["cited_phase2_supports_yes"] / n_c, 3), "supports_yes_or_partly": round((c["cited_phase2_supports_yes"] + c["cited_phase2_supports_partly"]) / n_c, 3),
       "relevant_yes_rate": round(c["cited_relevant_yes"] / n_c, 3), "speaker_ok": round(c["cited_speaker_ok"] / n_c, 3), "polarity_ok": round(c["cited_polarity_ok"] / n_c, 3), "context_ok": round(c["cited_context_ok"] / n_c, 3),
       "family_attribution_ok": round(c["cited_family_attr_ok"] / n_c, 3), "reviewer_best_segments_overlap_system": round(c["cited_reviewer_segments_overlap_system"] / n_c, 3), "underlying_fact_supported_by_transcript_yes": round(c["cited_phase1_fact_supported_yes"] / n_c, 3)},
       "abstained": {"abstention_justified_rate": round(c["abstained_justified_yes"] / n_a, 3), "reviewer_found_usable_evidence_in_phase1": round(c["abstained_reviewer_found_evidence_phase1"] / n_a, 3)},
       "concern_flag": "cited facts judged supported < 75%" if (c["cited_phase2_supports_yes"] / n_c) < 0.75 else "none", "note": "feasibility check; not statistically representative; do not tune rules on it"}
(d / "audit_scores.json").write_text(json.dumps(res, indent=1), encoding="utf-8"); print(json.dumps(res, indent=1))
