"""Assemble the round-5 training files: round-1 synthetic data + the natural encounters of rounds 2 and 4, with the labels CLEANED, to be trained from the BASE model.

  python -m finetune_slm.scripts.local.round5_build.build_round5_dataset

Why (docs/07_TRAINING_ROUND4.md, section 9): rounds 2 to 4 stacked a few hundred model-written labels on top of step 400 and every time recall rose while precision fell.
Two suspects are tested together here: (1) the model-written labels contain facts the verifier did not find supported; (2) stacking small rounds on an adapter
shifts its style. Round 5 therefore (a) removes from every natural label the facts the verifier marked unsupported, partially supported or contradicted (the label is
re-compacted afterwards; nothing else is edited), (b) drops encounters that still look doubtful, and (c) trains once from the base model on one mixed set.

An encounter of rounds 2 or 4 is used only when ALL hold:
  - it was verified; at most `--max-crit-omissions` (default 1) critical omissions were listed (a missing important fact teaches the model to omit it); at most `--max-bad` facts needed removing;
    at most 2 contradicted and at most 2 critical-error facts (more means the writer misunderstood the conversation);
  - after the removal, the automatic rules of round 4 (validate_labels.check_record) find nothing;
  - prompt + answer fit `--max-chars` characters.
Held-out situation families of round 2 and round 4 are never trained on; they form the natural validation set. The 20 hand-written scenarios and the locked test are not used.
Round-1 examples: all `oversampled_ids.txt` ids (the rare scenarios round 1 repeated) plus a random fill up to `--r1` unique examples.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "finetune_slm"))
sys.path.insert(0, str(ROOT / "finetune_slm/data/round1_synthetic/codec"))
from compact_codec import compact  # noqa: E402
from finetune_slm.evaluation.judge_eval.flatten import FIELDS, HISTORY_FIELDS, LIST_FIELDS, _fact, flatten  # noqa: E402
from finetune_slm.scripts.local.targeted_gen.validate_labels import check_record  # noqa: E402

HELD_OUT_ROUND2 = {"heavy_periods_anaemia", "gout_flare", "memory_concerns_spouse", "asthma_flare_inhaler"}
HELD_OUT_ROUND4 = {"sinusitis_after_cold", "kidney_stone_colic", "restless_legs_pregnancy", "bell_palsy_new", "hay_fever_season", "tennis_elbow_painter", "inguinal_hernia_lump"}
HELD_OUT = HELD_OUT_ROUND2 | HELD_OUT_ROUND4


def prune_full_label(full: dict, drop: set[str]) -> dict:
    """Remove the facts whose flatten id is in `drop` from a copy of the full label. The ids are numbered exactly as `flatten` numbers them (empty items are skipped)."""
    doc = copy.deepcopy(full)
    count: Counter = Counter()

    def keep(field: str, item) -> bool:
        fid = f"{field}[{count[field]}]"
        if _fact(fid, field, item):
            count[field] += 1
            return fid not in drop
        return True                                                       # an empty item has no id; leave it alone

    cc = doc.get("chief_complaint")
    if isinstance(cc, dict) and not keep("chief_complaint", cc):
        doc.pop("chief_complaint")
    hist = doc.get("medical_history")
    if isinstance(hist, dict):
        for h in HISTORY_FIELDS:
            if isinstance(hist.get(h), list):
                hist[h] = [x for x in hist[h] if keep(f"medical_history.{h}", x)]
    for field in LIST_FIELDS:
        value = doc.get(field)
        if isinstance(value, list):
            doc[field] = [x for x in value if keep(field, x)]
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", nargs="+", default=["finetune_slm/data/round2_natural/raw", "finetune_slm/data/round4_targeted/raw"])
    ap.add_argument("--out", default="finetune_slm/data/round5_clean_mix/run5")
    ap.add_argument("--r1", type=int, default=1900, help="round-1 unique examples")
    ap.add_argument("--nat-repeat", type=int, default=2, help="times each natural example appears in the training file (they are few; round 2 had about 27% natural views)")
    ap.add_argument("--max-bad", type=int, default=6)
    ap.add_argument("--max-crit-omissions", type=int, default=1, help="the rule used after a repair round in rounds 2 to 4")
    ap.add_argument("--max-chars", type=int, default=18000)
    ap.add_argument("--seed", type=int, default=20261128)
    a = ap.parse_args()
    template = (ROOT / "finetune_slm/data/round1_synthetic/prompt/short_prompt.txt").read_text(encoding="utf-8")
    nat_train, nat_val, why, dropped, fams, per_round = [], [], Counter(), Counter(), Counter(), Counter()
    facts_before = facts_after = 0
    for rawdir in a.raw:
        tag = "natural_round2" if "round2" in rawdir else "targeted_round4"
        for f in sorted((ROOT / rawdir).glob("*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            v = d.get("verify")
            if not v:
                why["not verified"] += 1
                continue
            if sum(1 for o in v["omissions"] if o.get("critical")) > a.max_crit_omissions:
                why["critical omissions"] += 1
                continue
            n_contra = sum(1 for b in v["bad"] if b["verdict"] == "contradicted")
            n_crit = sum(1 for b in v["bad"] if b.get("critical"))
            if len(v["bad"]) > a.max_bad or n_contra > 2 or n_crit > 2:
                why["too many doubtful facts"] += 1
                continue
            drop = {b["fid"] for b in v["bad"]}
            full = prune_full_label(d["full_label"], drop)
            n0, n1 = len(flatten(d["full_label"])), len(flatten(full))
            if n0 - n1 != len(drop):
                why["prune mismatch (skipped)"] += 1
                continue
            auto = check_record({"full_label": full, "turns_text": d["turns_text"]})
            if not auto["ok"]:
                why["automatic checks failed after removal"] += 1
                continue
            eid = d["spec"]["id"]
            user = template.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", "\n".join(d["turns_text"]))
            answer = json.dumps(compact(full), ensure_ascii=False, separators=(",", ":"))
            if len(user) + len(answer) > a.max_chars:
                why["too long"] += 1
                continue
            held = d["spec"]["family"] in HELD_OUT
            rec = {"id": eid, "source_batch": tag + "_clean", "split": "validation_natural" if held else "train", "scenario_group": ("nat_" if tag.startswith("natural") else "tgt_") + d["spec"]["family"],
                   "messages": [{"role": "user", "content": user}, {"role": "assistant", "content": answer}]}
            (nat_val if held else nat_train).append(rec)
            if not held:
                facts_before += n0; facts_after += n1; per_round[tag] += 1
                for b in v["bad"]:
                    dropped[b["verdict"]] += 1
    r1 = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/train.jsonl", encoding="utf-8")]
    over = {l.strip() for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/oversampled_ids.txt", encoding="utf-8") if l.strip()}
    must = [r for r in r1 if str(r["id"]) in over or str(r["id"]).lstrip("0") in {x.lstrip("0") for x in over}]
    rest = [r for r in r1 if r not in must]
    random.Random(a.seed).shuffle(rest)
    r1_pick = must + rest[: max(0, a.r1 - len(must))]
    rows = nat_train * a.nat_repeat + r1_pick
    random.Random(a.seed + 1).shuffle(rows)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "train_run5.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    val = [json.loads(l) for l in open(ROOT / "finetune_slm/data/round1_synthetic/data/validation.jsonl", encoding="utf-8")] + nat_val
    (out / "validation_run5.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in val) + "\n", encoding="utf-8")
    stats = {"natural_train": len(nat_train), "natural_train_by_source": dict(per_round), "round1_unique": len(r1_pick), "round1_from_oversampled_ids": len(must),
             "natural_repeat": a.nat_repeat, "train_total": len(rows), "validation_total": len(val), "validation_natural": len(nat_val), "excluded": dict(why),
             "facts_removed_from_training_labels": dict(dropped), "facts_before": facts_before, "facts_after": facts_after}
    (out / "build_stats.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
