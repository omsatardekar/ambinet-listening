"""Early-stop watcher for the P02 30-record run (P01 schema without model-written evidence). The rules are FIXED here, before the run, and must not be changed after results are seen.
They protect against a format collapse like the v2.1/v2.2 pilots; they never judge clinical quality, and they never fire for any other reason:

  V1  stop if the first record (00035) does not parse (any failure type, including the token cap)
  V2  stop if two of the first three completed records do not parse
  V3  stop if two of the first three PARSED records have 16 or more of the 18 clinical sections empty (v2.2 collapsed to 16-17 empty sections)

Checked after every completed record. The only action is terminating the runner process. Every check is appended to logs/P02_STOP_RULE_CHECKS.jsonl and the decision is written to
logs/P02_STOP_RULE_RESULT.json. After the third record no rule applies: all 30 records run and failures count in the headline score."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p02_common import EXP, categories, get_entities              # noqa: E402

RUN = "P02"
ORDER = ["00035", "00037", "00040"]
MAN = EXP / "evaluations" / RUN / "run_manifest.json"
LOG = EXP / "logs" / f"{RUN}_STOP_RULE_CHECKS.jsonl"
RESULT = EXP / "logs" / f"{RUN}_STOP_RULE_RESULT.json"


def runner_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_prompt.py' -and $_.CommandLine -match '" + RUN + "' -and $_.Name -match 'python' } | ForEach-Object { $_.ProcessId }"],
                       capture_output=True, text=True)
    return [int(x) for x in r.stdout.split()]


def empty_sections(eid):
    p = EXP / "outputs" / "parsed" / RUN / f"encounter_{eid}.json"
    o = json.loads(p.read_text(encoding="utf-8-sig"))
    return sum(1 for c in categories() if not get_entities(o, c))


def decide(recs):
    done = [i for i in ORDER if i in recs and recs[i].get("status") in ("parsed", "failed")]
    why, empties = [], {}
    if "00035" in done and recs["00035"].get("status") != "parsed":
        why.append(f"V1: record 1 did not parse ({recs['00035'].get('failure_type') or recs['00035'].get('finish_reason')})")
    if len(done) == 3:
        bad = [i for i in done if recs[i].get("status") != "parsed"]
        if len(bad) >= 2:
            why.append(f"V2: two of the first three records did not parse: {bad}")
    parsed = [i for i in done if recs[i].get("status") == "parsed"]
    for i in parsed:
        empties[i] = empty_sections(i)
    if len(done) == 3 and sum(v >= 16 for v in empties.values()) >= 2:
        why.append(f"V3: two of the first three parsed records have 16+ of 18 sections empty: {empties}")
    return done, why, empties


def main():
    started, seen = time.time(), -1
    while True:
        pids = runner_pids()
        recs = {}
        if MAN.exists():
            try:
                recs = json.loads(MAN.read_text(encoding="utf-8-sig"))["records"]
            except Exception:                                      # noqa: BLE001  (manifest being rewritten)
                recs = {}
        done, why, empties = decide(recs)
        if len(done) != seen:
            seen = len(done)
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"time": time.ctime(), "completed_first3": done, "status": {i: recs[i].get("status") for i in done}, "tokens": {i: recs[i].get("completion_tokens") for i in done},
                                    "empty_sections_of_18": empties, "triggered": why}) + "\n")
        if why:
            for p in pids:
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {p} -Force"], capture_output=True)
            RESULT.write_text(json.dumps({"stopped_by_rule": True, "reasons": why, "completed_first3": done, "terminated_pids": pids, "time": time.ctime()}, indent=1), encoding="utf-8")
            return
        if len(done) == 3:
            RESULT.write_text(json.dumps({"stopped_by_rule": False, "reasons": [], "completed_first3": done, "note": "first three records passed V1-V3; no rule applies to the rest of the run", "time": time.ctime()}, indent=1), encoding="utf-8")
            return
        if not pids and time.time() - started > 180:
            RESULT.write_text(json.dumps({"stopped_by_rule": False, "reasons": [], "completed_first3": done, "note": "runner no longer running before three records completed", "time": time.ctime()}, indent=1), encoding="utf-8")
            return
        time.sleep(15)


if __name__ == "__main__":
    main()
