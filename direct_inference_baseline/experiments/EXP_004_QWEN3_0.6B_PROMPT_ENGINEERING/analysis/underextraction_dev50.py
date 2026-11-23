"""EXP_004 P02 pre-work: READ-ONLY under-extraction analysis of P00 and P01 on the 50 prompt_dev ids ONLY (no validation, no test ids).
Aggregate counts only; no label strings are written to the output. Uses the existing evaluator functions unmodified."""
import json
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
ROOT = EXP4.parents[2]
sys.path.insert(0, str(ROOT))
from direct_inference_baseline.config import settings as S  # noqa: E402
from direct_inference_baseline.evaluation import evaluation_runner as ER  # noqa: E402
from direct_inference_baseline.evaluation import evidence_evaluator as EE  # noqa: E402
from direct_inference_baseline.evaluation.dataset_split import load_split  # noqa: E402
from direct_inference_baseline.evaluation.entity_matching import CATEGORIES, KEYS, entity_list, match_category, norm_text  # noqa: E402

split = json.loads((EXP4 / "experiments" / "split_v1.json").read_text(encoding="utf-8"))
IDS = split["prompt_dev_ids"]
assert len(IDS) == 50 and not set(IDS) & set(load_split("test")) and not set(IDS) & set(split["validation_ids"])
EXP3 = EXP4.parent / "EXP_003_QWEN3_0.6B_OPENVINO_GPU_DIRECT"
SRC = {"P00": (EXP3 / "parsed_predictions" / "exp_003_dev_100", None), "P01": (EXP4 / "outputs" / "P01_schema_focused_dev50" / "parsed_predictions" / "P01_schema_focused_dev50", None)}
res = {}
for ver, (d, _) in SRC.items():
    st = {c: Counter() for c in CATEGORIES}
    for eid in IDS:
        f = d / f"encounter_{eid}.json"
        gold = ER.load_gold(eid)
        tr = json.loads((S.INPUT_DIR / f"encounter_{eid}.json").read_text(encoding="utf-8"))
        full = " ".join(norm_text(s["text"]) for s in tr["segments"])
        pred = json.loads(f.read_text(encoding="utf-8")) if f.exists() else None
        for c in CATEGORIES:
            g = entity_list(gold, c)
            p = entity_list(pred, c) if pred else []
            st[c]["gold"] += len(g)
            st[c]["pred"] += len(p)
            st[c]["gold_records_with_items"] += bool(g)
            st[c]["pred_records_with_items"] += bool(p)
            m_s = match_category(g, p, c, fuzzy=False)
            m_f = match_category(g, p, c, fuzzy=True)
            st[c]["tp_strict"] += len(g) - len(m_s["fn_entities"])
            st[c]["tp_fuzzy"] += len(g) - len(m_f["fn_entities"])
            for k, _ in m_f["fn_entities"]:
                st[c]["fn_lexically_in_transcript"] += bool(EE.lexical_support(k, full, strict=False))
    res[ver] = {c: dict(v) for c, v in st.items()}
# gold-side structure (aggregate): items per encounter by category
tot_gold = {c: res["P00"][c]["gold"] for c in CATEGORIES}
out = {"ids": len(IDS), "per_version_per_category": res, "gold_items_per_encounter": {c: round(tot_gold[c] / 50, 2) for c in CATEGORIES}}
(EXP4 / "analysis" / "underextraction_dev50.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(f"{'category':38s} gold g/enc | P00 pred tp_s tp_f | P01 pred tp_s tp_f | FN-in-transcript(P01)")
for c in CATEGORIES:
    a, b = res["P00"][c], res["P01"][c]
    print(f"{c:38s} {a['gold']:4d} {tot_gold[c]/50:5.1f} | {a['pred']:4d} {a['tp_strict']:3d} {a['tp_fuzzy']:3d} | {b['pred']:4d} {b['tp_strict']:3d} {b['tp_fuzzy']:3d} | {b.get('fn_lexically_in_transcript', 0)}/{b['gold'] - b['tp_fuzzy']}  recs gold/pred {b['gold_records_with_items']}/{b['pred_records_with_items']}")
