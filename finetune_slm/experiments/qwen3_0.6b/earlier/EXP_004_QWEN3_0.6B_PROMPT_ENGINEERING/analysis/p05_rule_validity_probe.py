"""EXP_004 P05 pre-work (READ-ONLY, ZERO INFERENCE, prompt_dev 50 ids only): do the planned retrieval filter rules agree with how the gold labels cite evidence?
For every gold item (the 50 prompt_dev labels) and its gold-cited segment set, measure per category:
  speaker class of the NON-QUESTION cited segments, share of cited sets that are question-only / question+answer, negation cue in the cited set (negative findings), kin terms in family-history vs own-history cited sets,
  and lexical reachability (does some gold-cited segment pass the candidate-generation test used by the retriever?).
Development choices made from these numbers are therefore calibrated on prompt_dev and are NOT independent of it."""
import json
import re
import sys
import types
from collections import Counter, defaultdict
from pathlib import Path

try:
    import dotenv  # noqa
except ImportError:
    sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda *a, **k: False)
sys.dont_write_bytecode = True
EXP4 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP4 / "experiments"))
sys.path.insert(0, str(EXP4.parents[2]))
from common import S, SPLIT  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, entity_list, norm_text  # noqa: E402
import p05_retrieval as R  # noqa: E402

IDS = SPLIT["prompt_dev_ids"]
assert not set(IDS) & set(load_split("test")) and not set(IDS) & set(SPLIT["validation_ids"])
mm = lambda s: f"{int(s)//60:02d}:{int(s)%60:02d}"
cls = lambda role: "clinician" if role in R.CLIN else "patient_side" if role in R.PAT_SIDE else "other"
st = defaultdict(Counter)
for eid in IDS:
    tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8")); segs = tr["segments"]; enc = R.Enc(segs)
    gold = ER.load_gold(eid)
    seg_of = {}
    for r in gold.get("clinical_evidence", []):
        t = norm_text(r["transcript_text"])
        hit = [i for i, s in enumerate(segs) if t == norm_text(s["text"]) and s["speaker_id"] == r["speaker_id"] and mm(s["start_seconds"]) == r["start_timestamp"]]
        seg_of[r["evidence_id"]] = hit[0] if hit else None
    for c in CATEGORIES:
        for e in entity_list(gold, c):
            G = sorted({seg_of[x] for x in (e.get("evidence_ids") or []) if seg_of.get(x) is not None})
            if not G:
                continue
            k = st[c]; k["items"] += 1; k["gold_segments"] += len(G)
            nonq = [i for i in G if not enc.q[i]]
            k["sets_question_only"] += not nonq
            k["sets_with_question_and_nonquestion"] += bool(nonq) and len(nonq) < len(G)
            for i in nonq:
                k[f"nonq_class_{cls(enc.role[i])}"] += 1
            k["sets_with_any_nonq_role_matching_patient_side"] += any(enc.role[i] in R.PAT_SIDE for i in nonq)
            k["sets_with_any_nonq_role_clinician"] += any(enc.role[i] in R.CLIN for i in nonq)
            k["sets_with_negation_cue"] += any(R.has_neg(enc.raw[i]) for i in G)
            k["sets_with_kin_term"] += any(R.has_kin(enc.raw[i]) for i in G)
            q = R.query_fields(c, e)
            cov = max((R.field_cov(enc, stems_, i)[0] for i in G for stems_ in q.values() if stems_), default=0.0)
            k["reachable_cov_ge_0.6"] += cov >= 0.6
            k["reachable_cov_ge_0.5"] += cov >= 0.5
out = {c: dict(v) for c, v in st.items()}
(EXP4 / "analysis" / "p05_rule_validity_probe.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"{'category':38s} items  q-only  q+nonq | nonq roles: patient/clin/other | neg-cue kin-term reach>=.6")
for c in CATEGORIES:
    k = st[c]
    if not k["items"]:
        continue
    n = k["items"]; nn = sum(k[f"nonq_class_{x}"] for x in ("patient_side", "clinician", "other")) or 1
    print(f"{c:38s} {n:5d} {k['sets_question_only']/n:6.0%} {k['sets_with_question_and_nonquestion']/n:7.0%} | {k['nonq_class_patient_side']/nn:6.0%} {k['nonq_class_clinician']/nn:6.0%} {k['nonq_class_other']/nn:6.0%} | {k['sets_with_negation_cue']/n:6.0%} {k['sets_with_kin_term']/n:6.0%} {k['reachable_cov_ge_0.6']/n:6.0%}")
