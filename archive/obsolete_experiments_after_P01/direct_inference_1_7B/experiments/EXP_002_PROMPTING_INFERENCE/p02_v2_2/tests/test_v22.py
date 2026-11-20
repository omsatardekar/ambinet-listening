"""Unit tests for the P02 v2.2 preparation pipeline. Standard library only; no model, no OpenVINO, no network.
Run:  python -B -I tests/test_v22.py          (from p02_v2_2/)
Synthetic transcripts use invented text. Tests that touch real data read only the 50 authorised dev ids of the corrected dataset, read-only."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "code"))
import convert_gold as CG                                           # noqa: E402
import evaluate_v22 as EV                                           # noqa: E402
from evidence_resolver import EvidenceResolver                      # noqa: E402
from materialiser import materialise                                # noqa: E402
import v22_common as V                                              # noqa: E402

SYN = {"encounter_id": "99999", "segments": [
    {"segment_id": "SEG0001", "speaker_id": "person_1", "role": "DOCTOR", "start_seconds": 1.2, "end_seconds": 4.9, "text": "What brings you in today?"},
    {"segment_id": "SEG0002", "speaker_id": "person_2", "role": "PATIENT", "start_seconds": 62.5, "end_seconds": 70.1, "text": "My left wrist hurts since Monday. I take ibuprofen 400 milligrams."},
    {"segment_id": "SEG0003", "speaker_id": "person_3", "role": "NURSE", "start_seconds": 71.0, "end_seconds": 75.0, "text": "Our chart says ibuprofen 200 milligrams."},
    {"segment_id": "SEG0004", "speaker_id": "person_1", "role": "DOCTOR", "start_seconds": 76.0, "end_seconds": 79.0, "text": "Any numbness or swelling?"},
    {"segment_id": "SEG0005", "speaker_id": "person_2", "role": "PATIENT", "start_seconds": 80.0, "end_seconds": 83.0, "text": "No numbness. No swelling."},
    {"segment_id": "SEG0006", "speaker_id": "person_1", "role": "DOCTOR", "start_seconds": 84.0, "end_seconds": 90.0, "text": "I will arrange a wrist x-ray. Please come back in a week."}]}

MINIMAL = {"negative_findings": [{"finding": "numbness", "refs": ["SEG0004", "SEG0005"], "by": "patient"}, {"finding": "swelling", "refs": ["SEG0005"]}],
           "medications": [{"name": "ibuprofen", "status": "currently_used", "refs": ["SEG0002", "SEG0003"], "by": "patient"}],
           "clinical_uncertainties": [{"type": "medication_discrepancy", "description": "ibuprofen: patient states 400 mg; nurse states 200 mg", "related": ["medications[0]"], "refs": ["SEG0002", "SEG0003"]}],
           "chief_complaint": {"value": "wrist pain", "refs": ["SEG0002"]},
           "symptoms": [{"name": "wrist pain", "body_site": "left wrist", "onset": "since Monday", "refs": ["SEG0002"]}]}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TestResolver(unittest.TestCase):
    def setUp(self):
        self.r = EvidenceResolver(SYN, max_refs=2)

    def test_exact_original_content(self):
        x = self.r.resolve("SEG0002")
        self.assertTrue(x.ok)
        self.assertEqual((x.text, x.speaker_id, x.role, x.start_seconds, x.end_seconds), (SYN["segments"][1]["text"], "person_2", "patient", 62.5, 70.1))
        self.assertEqual((x.start_timestamp, x.end_timestamp), ("01:02", "01:10"))        # rounded down, gold convention

    def test_invalid_references_are_flagged_not_repaired(self):
        for bad in ("SEG9999", "seg0002", "SEG002", " SEG0002", "EV_001", "", None, 2, ["SEG0002"]):
            x = self.r.resolve(bad)
            self.assertFalse(x.ok, bad)
            self.assertIsNone(x.segment_id)
            self.assertEqual(x.ref, bad)                                               # the original value stays visible

    def test_excessive_duplicate_and_missing_flags_keep_every_ref(self):
        refs, fl = self.r.resolve_fact(["SEG0001", "SEG0002", "SEG0003", "SEG0002"], "symptoms[0]")
        kinds = sorted(f.kind for f in fl)
        self.assertEqual(kinds, ["duplicate_reference", "excessive_references"])
        self.assertEqual(len(refs), 4)                                                  # nothing dropped
        _, fl = self.r.resolve_fact([], "x[0]")
        self.assertEqual([f.kind for f in fl], ["no_references"])
        _, fl = self.r.resolve_fact("SEG0001", "x[0]")
        self.assertEqual([f.kind for f in fl], ["refs_not_a_list"])

    def test_evidence_for_keeps_invalid(self):
        out = self.r.evidence_for(["SEG0003", "SEG0001", "SEG7777"])
        self.assertEqual([o["ref"] for o in out], ["SEG0001", "SEG0003", "SEG7777"])    # transcript order, invalid last, none skipped
        self.assertFalse(out[-1]["ok"])

    def test_speaker_table(self):
        self.assertEqual(self.r.speaker_table(), [{"speaker_id": "person_1", "role": "doctor"}, {"speaker_id": "person_2", "role": "patient"}, {"speaker_id": "person_3", "role": "nurse"}])


class TestMaterialiser(unittest.TestCase):
    def test_full_structure_defaults_and_evidence(self):
        m = materialise(copy.deepcopy(MINIMAL), SYN)
        f = m.full
        self.assertEqual(list(f)[:3] + [list(f)[-1]], ["encounter_id", "extraction_status", "encounter_metadata", "clinical_evidence"])
        self.assertNotIn("quality_checks", f)                                         # deliberately not derived
        top = list(V.frozen_schema()["top_level_keys"])
        top.remove("quality_checks")
        self.assertEqual(list(f), top)
        nf = f["negative_findings"][0]
        self.assertEqual((nf["status"], nf["assertion"], nf["temporality"], nf["confidence"]), ("absent", "negative", "current", None))
        self.assertEqual(list(nf), V.category_keys("negative_findings"))                # frozen key order
        self.assertEqual(f["symptoms"][0]["temporality"], "current")
        self.assertEqual(f["symptoms"][0]["certainty"], "certain")
        self.assertEqual(f["medications"][0]["dose"], None)
        self.assertEqual([e["evidence_id"] for e in f["clinical_evidence"]], ["EV_001", "EV_002", "EV_003", "EV_004"])   # transcript order
        self.assertEqual([e["transcript_text"] for e in f["clinical_evidence"]][0], SYN["segments"][1]["text"])
        self.assertIn("medications[0]", f["clinical_evidence"][0]["supports"])
        self.assertEqual(f["negative_findings"][0]["evidence_ids"], ["EV_003", "EV_004"])      # SEG0004, SEG0005 -> third and fourth cited segment
        self.assertEqual(f["negative_findings"][1]["evidence_ids"], ["EV_004"])
        self.assertEqual(f["clinical_evidence"][3]["supports"], ["negative_findings[0]", "negative_findings[1]"])
        self.assertEqual(f["negative_findings"][0]["reported_by"], "patient")                # explicit
        self.assertEqual(f["negative_findings"][1]["reported_by"], "patient")                # derived (single cited role)
        self.assertEqual(m.flag_counts().get("invalid_reference", 0), 0)

    def test_every_clinical_category_exists_in_the_materialised_record(self):
        f = materialise(MINIMAL, SYN).full
        for cat in V.categories():
            self.assertIsInstance(V.get_entities(f, cat) if cat != "chief_complaint" else [f["chief_complaint"]], list)
        self.assertEqual(sorted(f["medical_history"]), ["family_history", "past_medical_history", "social_history", "surgical_history"])

    def test_invalid_reference_kept_and_flagged_no_evidence_record(self):
        c = copy.deepcopy(MINIMAL)
        c["symptoms"][0]["refs"] = ["SEG0002", "SEG0042"]
        m = materialise(c, SYN)
        self.assertEqual(m.full["symptoms"][0]["evidence_ids"][1], "SEG0042")           # original string stays
        self.assertIn("invalid_reference", m.flag_counts())
        self.assertNotIn("SEG0042", [e["transcript_text"] for e in m.full["clinical_evidence"]])
        self.assertEqual(m.stats["refs_invalid"], 1)

    def test_speaker_rules(self):
        c = {"symptoms": [{"name": "a", "refs": ["SEG0002"]},                        # unique role -> derived
                          {"name": "b", "refs": ["SEG0004", "SEG0005"]},             # mixed roles -> NOT derived, flagged
                          {"name": "c", "refs": ["SEG0005"], "by": "doctor"},        # explicit, not among cited roles -> kept, flagged
                          {"name": "d", "refs": ["SEG0005"], "by": "person_2"},      # a speaker id -> kept, flagged
                          {"name": "e", "refs": ["SEG0005"], "by": None}]}           # explicit null stays null
        m = materialise(c, SYN)
        s = [x["reported_by"] for x in m.full["symptoms"]]
        self.assertEqual(s, ["patient", None, "doctor", "person_2", None])
        k = m.flag_counts()
        self.assertEqual((k["speaker_unresolved"], k["by_not_in_refs_roles"], k["by_is_speaker_id"]), (1, 1, 1))

    def test_responsible_person_is_never_derived(self):
        c = {"clinical_actions": [{"action_type": "investigation", "description": "arrange wrist x-ray", "status": "planned", "refs": ["SEG0006"]}]}
        m = materialise(c, SYN)
        self.assertIsNone(m.full["clinical_actions"][0]["responsible_person"])
        self.assertIn("missing_required", m.flag_counts())
        c["clinical_actions"][0]["responsible"] = "doctor"
        self.assertEqual(materialise(c, SYN).full["clinical_actions"][0]["responsible_person"], "doctor")

    def test_unknown_keys_enum_and_type_problems_are_flagged_not_repaired(self):
        c = {"symptoms": [{"name": "a", "refs": ["SEG0002"], "foo": 1, "status": "Present", "category": "bone"}], "invented_section": [1], "medications": [{"name": "x", "status": "planned", "route": "iv", "refs": ["SEG0002"]}]}
        m = materialise(c, SYN)
        k = m.flag_counts()
        self.assertEqual(k["unknown_key"], 1)
        self.assertEqual(k["unknown_top_level_key"], 1)
        self.assertEqual(k["enum_violation"], 3)                                       # status, category, route
        self.assertEqual(m.full["symptoms"][0]["status"], "Present")                    # value kept as given
        self.assertEqual({u["key"] for u in m.unmapped}, {"foo", "invented_section"})   # nothing silently discarded

    def test_symptom_status_temporality_defaults_and_inconsistency(self):
        c = {"symptoms": [{"name": "a", "status": "resolved", "refs": ["SEG0002"]}, {"name": "b", "status": "resolved", "temporality": "past", "refs": ["SEG0002"]},
                          {"name": "c", "status": "resolved", "temporality": "current", "refs": ["SEG0002"]}]}
        m = materialise(c, SYN)
        self.assertEqual([x["temporality"] for x in m.full["symptoms"]], ["resolved", "past", "current"])
        self.assertEqual(m.flag_counts()["status_temporality_inconsistent"], 1)

    def test_nested_objects_restored_and_related_checked(self):
        c = {"symptoms": [{"name": "a", "duration": {"value": 2, "unit": "weeks"}, "refs": ["SEG0002"]}],
             "clinical_uncertainties": [{"type": "date_uncertain", "description": "x", "related": ["symptoms[0]", "symptoms[5]", "bogus"], "refs": ["SEG0002"]}]}
        m = materialise(c, SYN)
        self.assertEqual(m.full["symptoms"][0]["duration"], {"value": 2, "unit": "weeks", "normalized": None})
        self.assertEqual(m.flag_counts()["related_unresolved"], 2)

    def test_two_conflicting_doses_are_representable_with_the_dose_left_null(self):
        m = materialise(MINIMAL, SYN)
        self.assertIsNone(m.full["medications"][0]["dose"])
        self.assertEqual(m.full["clinical_uncertainties"][0]["type"], "medication_discrepancy")
        self.assertIn("400 mg", m.full["clinical_uncertainties"][0]["description"])
        self.assertIn("200 mg", m.full["clinical_uncertainties"][0]["description"])

    def test_non_object_input(self):
        m = materialise(["x"], SYN)
        self.assertEqual(m.flag_counts(), {"compact_not_an_object": 1})


class TestGoldConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = V.authorised_ids()

    def test_access_guard(self):
        non_dev = next(f"{i:05d}" for i in range(1, 500) if f"{i:05d}" not in set(self.ids))
        for bad in (non_dev, "99999", "abc", "../x"):
            with self.assertRaises((PermissionError, ValueError)):
                V.load_gold(bad)
            with self.assertRaises((PermissionError, ValueError)):
                V.load_transcript(bad)

    def test_fifty_ids_and_no_mapping_failures(self):
        self.assertEqual(len(self.ids), 50)
        tot = fails = 0
        for eid in self.ids:
            g, t = V.load_gold(eid), V.load_transcript(eid)
            m, f = CG.build_ev_map(g, t)
            tot += len(g["clinical_evidence"])
            fails += len(f)
            self.assertEqual(len(m), len(g["clinical_evidence"]))
        self.assertEqual((tot, fails), (1772, 0))

    def test_round_trip_is_exact_for_all_50_in_both_variants(self):
        for eid in self.ids:
            g, t = V.load_gold(eid), V.load_transcript(eid)
            m, _ = CG.build_ev_map(g, t)
            for omit in (False, True):
                c, info = CG.to_compact(g, t, m, omit_derivable_by=omit)
                d, _ = CG.roundtrip(g, c, t)
                self.assertEqual(d, [], f"{eid} omit_by={omit}: {d[:3]}")
                self.assertEqual(info["failed_ref_mappings"], 0)

    def test_compact_gold_content(self):
        for eid in self.ids[:12]:
            g, t = V.load_gold(eid), V.load_transcript(eid)
            m, _ = CG.build_ev_map(g, t)
            c, _ = CG.to_compact(g, t, m)
            for k in ("clinical_evidence", "quality_checks", "encounter_metadata", "extraction_status", "encounter_id"):
                self.assertNotIn(k, c)
            for cat in V.categories():                                                  # no clinical fact dropped
                got = len(c.get("medical_history", {}).get(cat.split(".")[1], [])) if "." in cat else (len(c.get(cat, [])) if cat != "chief_complaint" else int("chief_complaint" in c))
                self.assertEqual(got, len(V.get_entities(g, cat)), (eid, cat))

            def walk(x, path=""):
                if isinstance(x, dict):
                    for k, v in x.items():
                        if k == "by" and v is None:
                            continue
                        self.assertNotIn(v, (None, "", [], {}), f"{eid} {path}/{k}")
                        walk(v, f"{path}/{k}")
                elif isinstance(x, list):
                    for i, v in enumerate(x):
                        walk(v, f"{path}[{i}]")
            walk(c)
            for k in c:
                self.assertIn(k, V.compact_schema()["model_emits_top_level_keys_in_this_order"])

    def test_round_trip_detects_damage(self):
        eid = self.ids[0]
        g, t = V.load_gold(eid), V.load_transcript(eid)
        m, _ = CG.build_ev_map(g, t)
        c, _ = CG.to_compact(g, t, m)
        c2 = copy.deepcopy(c)
        c2["symptoms"][0]["refs"] = c2["symptoms"][0]["refs"][:-1] or ["SEG0001"]
        self.assertNotEqual(CG.roundtrip(g, c2, t)[0], [])
        c3 = copy.deepcopy(c)
        c3["negative_findings"][0]["finding"] = "zzz"
        self.assertNotEqual(CG.roundtrip(g, c3, t)[0], [])

    def test_original_dataset_files_are_untouched_by_conversion(self):
        files = [V.INPUT_DIR / f"encounter_{i}.json" for i in self.ids[:10]] + [V.LABEL_DIR / f"encounter_{i}.json" for i in self.ids[:10]]
        before = [sha(f) for f in files]
        for eid in self.ids[:10]:
            g, t = V.load_gold(eid), V.load_transcript(eid)
            m, _ = CG.build_ev_map(g, t)
            CG.to_compact(g, t, m)
            CG.roundtrip(g, CG.to_compact(g, t, m)[0], t)
        self.assertEqual(before, [sha(f) for f in files])

    def test_gold_metadata_equals_the_transcript_speaker_table(self):
        for eid in self.ids:
            g, t = V.load_gold(eid), V.load_transcript(eid)
            r = EvidenceResolver(t)
            self.assertEqual(g["encounter_metadata"]["primary_speakers"], [{"speaker_id": s["speaker_id"], "role": s["role"], "role_confidence": None} for s in r.speaker_table()])


class TestEvaluator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = V.authorised_ids()[:12]

    def _gold_run(self, fmt):
        return EV.gold_records(self.ids, fmt)

    def test_gold_against_itself_is_perfect(self):
        for fmt in ("compact", "full"):
            A = EV.evaluate(self._gold_run(fmt), fmt)
            t = A["entities_tier1_all_records_failed_as_zero"]
            self.assertEqual((t["micro"]["precision"], t["micro"]["recall"], t["micro"]["f1"]), (1.0, 1.0, 1.0), fmt)
            for cat, v in t["per_category"].items():
                if v["gold"]:
                    self.assertEqual((v["precision"], v["recall"], v["f1"]), (1.0, 1.0, 1.0), (fmt, cat))
            self.assertEqual(A["evidence_reference_validity"]["valid_share"], 1.0)
            ov = A["evidence_reference_overlap_with_gold_on_matched_facts"]
            self.assertEqual((ov["precision_vs_gold_segments"], ov["recall_of_gold_segments"], ov["pairs_with_identical_segment_set_share"]), (1.0, 1.0, 1.0))
            self.assertEqual(A["medication_discrepancy"]["fully_handled"], A["medication_discrepancy"]["gold_cases"])
            self.assertEqual(A["planned_medication"]["recall_by_name_and_status_planned"], 1.0)

    def test_failed_record_counts_as_zero_predictions(self):
        run = self._gold_run("compact")
        run[self.ids[0]] = {"id": self.ids[0], "status": "failed", "obj": None, "failure": "truncated", "gen": {"finish_reason": "length"}}
        A = EV.evaluate(run, "compact")
        t1, t2 = A["entities_tier1_all_records_failed_as_zero"], A["entities_tier2_parsed_records_only"]
        self.assertLess(t1["micro"]["recall"], 1.0)
        self.assertEqual(t1["micro"]["precision"], 1.0)
        self.assertEqual(t2["micro"]["recall"], 1.0)
        self.assertEqual(A["validity"]["failed"], 1)
        self.assertEqual(A["validity"]["truncated_at_token_cap"], 1)

    def test_missing_negative_findings_lower_negative_recall_only(self):
        run = self._gold_run("compact")
        for r in run.values():
            r["obj"].pop("negative_findings", None)
        A = EV.evaluate(run, "compact")
        nf = A["entities_tier1_all_records_failed_as_zero"]["negative_findings"]
        self.assertEqual(nf["recall"], 0.0)
        self.assertEqual(A["entities_tier1_all_records_failed_as_zero"]["per_category"]["symptoms"]["f1"], 1.0)

    def test_extra_invented_negative_is_a_false_positive_and_flagged_unsupported(self):
        run = self._gold_run("compact")
        eid = self.ids[0]
        seg = V.load_transcript(eid)["segments"][2]["segment_id"]
        run[eid]["obj"].setdefault("negative_findings", []).append({"finding": "zebra stripes", "refs": [seg]})
        A = EV.evaluate(run, "compact")
        nf = A["entities_tier1_all_records_failed_as_zero"]["negative_findings"]
        self.assertEqual(nf["fp"], 1)
        self.assertLess(nf["precision"], 1.0)
        ind = A["unsupported_claim_indicators_lexical_only"]["indicators"]
        self.assertGreaterEqual(ind["no_lexical_overlap_with_cited_text"]["count"], 1)

    def test_invalid_reference_is_counted(self):
        run = self._gold_run("compact")
        eid = self.ids[0]
        run[eid]["obj"]["symptoms"][0]["refs"] = run[eid]["obj"]["symptoms"][0]["refs"] + ["SEG9999"]
        A = EV.evaluate(run, "compact")
        self.assertEqual(A["evidence_reference_validity"]["refs_invalid"], 1)
        self.assertLess(A["evidence_reference_overlap_with_gold_on_matched_facts"]["precision_vs_gold_segments"] or 1, 1.0 + 1e-9)

    def test_discrepancy_handling_cases(self):
        gold = {"medications": [{"name": "ramipril", "normalized_name": "Ramipril", "dose": None, "status": "currently_used"}],
                "clinical_uncertainties": [{"type": "medication_discrepancy", "description": "ramipril: patient states 5 mg; nurse states 10 mg. Current dose not established.", "related_entities": ["medications[0]"]}]}
        good = {"medications": [{"name": "ramipril", "normalized_name": "Ramipril", "dose": None}],
                "clinical_uncertainties": [{"type": "medication_discrepancy", "description": "ramipril: patient says 5 milligrams, nurse says 10 milligrams", "related_entities": ["medications[0]"]}]}
        chose = {"medications": [{"name": "ramipril", "normalized_name": "Ramipril", "dose": "5 mg"}], "clinical_uncertainties": []}
        half = {"medications": [{"name": "ramipril", "normalized_name": "Ramipril", "dose": "5 mg"}],
                "clinical_uncertainties": [{"type": "medication_discrepancy", "description": "dose differs", "related_entities": ["medications[0]"]}]}
        self.assertEqual(EV.discrepancy_handling(gold, good)["fully_handled"], 1)
        c = EV.discrepancy_handling(gold, chose)
        self.assertEqual((c["detected"], c["fully_handled"]), (0, 0))
        h = EV.discrepancy_handling(gold, half)
        self.assertEqual((h["detected"], h["both_values_named"], h["dose_left_null"], h["fully_handled"]), (1, 0, 0, 0))

    def test_unsupported_indicators_catch_the_v21_failure_patterns(self):
        tr = SYN
        res = EvidenceResolver(tr)
        pred = {"medical_history": {"social_history": [{"category": "smoking", "description": "none", "status": "none", "evidence_ids": ["EV_001"]}], "past_medical_history": [], "surgical_history": [], "family_history": []},
                "medications": [{"name": "ibuprofen", "route": "oral", "dose": "900 mg", "evidence_ids": ["EV_001"]}],
                "follow_up": [{"type": "consultation", "time_reference": "2023-10-01", "evidence_ids": ["EV_001"]}],
                "clinical_evidence": []}
        ctx = {"res": res, "ev_to_seg": {"EV_001": "SEG0002"}}
        c, ex = EV.unsupported_indicators(pred, tr, ctx, "compact")
        self.assertEqual(c["habit_not_mentioned_anywhere_in_transcript"], 1)
        self.assertEqual(c["date_not_in_transcript"], 1)
        self.assertGreaterEqual(c["number_not_in_cited_text"], 1)                     # 900 (and the invented date's digits) are not in the cited line
        self.assertTrue(any("900" in e["detail"] for e in ex["number_not_in_cited_text"]))
        self.assertEqual(c["route_without_oral_cue_in_cited_text"], 1)

    def test_full_format_evidence_block_audit_on_gold(self):
        A = EV.evaluate(self._gold_run("full"), "full")
        a = A["full_format_evidence_block_audit"][self.ids[0]]
        self.assertEqual((a["text_mismatch"], a["speaker_mismatch"], a["start_timestamp_mismatch"], a["end_timestamp_mismatch"], a["records_with_unknown_segment"]), (0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
