"""Unit/integration tests for the P02 evidence backfill. Standard library only; no model. Run: python -B -I test_p02.py"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_evidence import backfill                       # noqa: E402
from convert_gold import build_ev_map                        # noqa: E402
from p02_common import authorised_ids, categories, get_entities, load_gold, load_transcript   # noqa: E402


def gold_as_model_output(eid):
    """what a perfect P02 model would write: gold, but evidence_ids = segment ids and clinical_evidence = []"""
    g, tr = load_gold(eid), load_transcript(eid)
    m, _ = build_ev_map(g, tr)
    p = copy.deepcopy(g)
    for cat in categories():
        for e in get_entities(p, cat):
            if isinstance(e, dict):
                e["evidence_ids"] = [m[x] for x in e.get("evidence_ids", []) if x in m]
    p["clinical_evidence"] = []
    return g, p, tr


class T(unittest.TestCase):
    def test_roundtrip_gold_all_50(self):
        """gold -> segment ids -> backfill must give back the gold evidence block and gold EV references (same ids, same order, same records) for every dev record"""
        bad = []
        for eid in authorised_ids():
            g, p, tr = gold_as_model_output(eid)
            full, flags, st = backfill(p, tr)
            ref = [c for c in (get_entities(g, c) for c in categories())]
            hard = [f for f in flags if f["kind"] != "excessive_references"]      # >4 refs is a warning only; gold itself exceeds it
            if hard:
                bad.append((eid, "flags", hard[:2]))
            ge = [(e["evidence_id"], e["speaker_id"], str(e["speaker_role"]).lower(), e["transcript_text"], e["start_timestamp"], e["end_timestamp"]) for e in g["clinical_evidence"]]
            fe = [(e["evidence_id"], e["speaker_id"], e["speaker_role"], e["transcript_text"], e["start_timestamp"], e["end_timestamp"]) for e in full["clinical_evidence"]]
            if sorted(x[1:] for x in ge) != sorted(x[1:] for x in fe):
                bad.append((eid, "evidence records differ"))
        self.assertEqual(bad, [], bad[:3])

    def test_invalid_reference_kept_and_flagged(self):
        g, p, tr = gold_as_model_output("00168")
        p["symptoms"][0]["evidence_ids"] = ["SEG9999", "seg0001", "EV_001", 7]
        full, flags, st = backfill(p, tr)
        kinds = [f["kind"] for f in flags]
        self.assertEqual(kinds.count("invalid_reference"), 3)
        self.assertEqual(kinds.count("non_string_reference"), 1)
        self.assertEqual(full["symptoms"][0]["evidence_ids"], ["SEG9999", "seg0001", "EV_001", 7])      # nothing repaired or dropped

    def test_model_written_evidence_is_reported_and_replaced(self):
        g, p, tr = gold_as_model_output("00168")
        p["clinical_evidence"] = [{"evidence_id": "EV_001", "transcript_text": "made up"}]
        full, flags, st = backfill(p, tr)
        self.assertIn("model_wrote_evidence_records", [f["kind"] for f in flags])
        self.assertNotEqual(full["clinical_evidence"][0].get("transcript_text"), "made up")

    def test_no_reference_flagged_and_other_fields_untouched(self):
        g, p, tr = gold_as_model_output("00168")
        p["symptoms"][0]["evidence_ids"] = []
        q = copy.deepcopy(p)
        full, flags, st = backfill(p, tr)
        self.assertIn("no_references", [f["kind"] for f in flags])
        self.assertEqual(p, q)                                                                            # input is not mutated
        self.assertEqual(full["quality_checks"], q["quality_checks"])
        self.assertEqual(full["encounter_metadata"], q["encounter_metadata"])

    def test_excess_references_kept(self):
        g, p, tr = gold_as_model_output("00168")
        ids = [s["segment_id"] for s in tr["segments"]][:6]
        p["symptoms"][0]["evidence_ids"] = ids
        full, flags, st = backfill(p, tr)
        self.assertIn("excessive_references", [f["kind"] for f in flags])
        self.assertEqual(len(full["symptoms"][0]["evidence_ids"]), 6)

    def test_ev_ids_in_transcript_order_and_supports(self):
        g, p, tr = gold_as_model_output("00168")
        full, flags, st = backfill(p, tr)
        order = {s["segment_id"]: i for i, s in enumerate(tr["segments"])}
        texts = [e["transcript_text"] for e in full["clinical_evidence"]]
        self.assertEqual([e["evidence_id"] for e in full["clinical_evidence"]], [f"EV_{i:03d}" for i in range(1, len(texts) + 1)])
        self.assertTrue(all(e["supports"] for e in full["clinical_evidence"]))
        pos = [next(i for s, i in order.items() if tr["segments"][i]["text"] == t) for t in texts]
        self.assertEqual(pos, sorted(pos))

    def test_not_a_dict(self):
        full, flags, st = backfill([], load_transcript("00168"))
        self.assertEqual(flags[0]["kind"], "record_not_an_object")


if __name__ == "__main__":
    unittest.main(verbosity=2)
