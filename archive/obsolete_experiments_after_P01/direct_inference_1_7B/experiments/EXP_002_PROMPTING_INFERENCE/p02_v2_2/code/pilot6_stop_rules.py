"""Early-stop watcher for the P02 v2.2 six-record pilot. The rules are FIXED here, before the run, exactly as in P02_v2_2_PROPOSAL.md section 6 and must not be changed after results are seen:

  R1  record 1 (00168): stop if it exceeds 2,500 output tokens, OR does not parse, OR cites a segment id that is not in its transcript
  R2  stop if any two of the first three records reach the token cap (finish_reason == length)
  R3  stop if any one of the first three records reaches the cap while another of the first three exceeds 3,300 output tokens

Checked after every completed record. The only action is terminating the runner process; nothing is read except the run manifest and the parsed output of record 1.
Every check is appended to logs/P02_v2_2_pilot6_STOP_RULE_CHECKS.jsonl and the decision to logs/P02_v2_2_pilot6_STOP_RULE_RESULT.json."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from materialiser import materialise                              # noqa: E402
from v22_common import EXP, load_transcript                       # noqa: E402

RUN = "P02_v2_2_pilot6"
ORDER = ["00168", "00204", "00037", "00092", "00152", "00157"]
CAP, HIGH, R1_TOKENS = 4096, 3300, 2500
MAN = EXP / "evaluations" / RUN / "run_manifest.json"
LOG = EXP / "logs" / f"{RUN}_STOP_RULE_CHECKS.jsonl"
RESULT = EXP / "logs" / f"{RUN}_STOP_RULE_RESULT.json"


def runner_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_prompt.py' -and $_.CommandLine -match '" + RUN + "' -and $_.Name -match 'python' } | ForEach-Object { $_.ProcessId }"],
                       capture_output=True, text=True)
    return [int(x) for x in r.stdout.split()]


def r1_problem(recs):
    r = recs["00168"]
    if r.get("status") != "parsed":
        return f"record 1 did not parse (status {r.get('status')}, {r.get('failure_type') or r.get('parse_status')})"
    if (r.get("completion_tokens") or 0) > R1_TOKENS:
        return f"record 1 used {r.get('completion_tokens')} output tokens (> {R1_TOKENS})"
    p = EXP / "outputs" / "parsed" / RUN / "encounter_00168.json"
    m = materialise(json.loads(p.read_text(encoding="utf-8-sig")), load_transcript("00168"))
    if m.stats["refs_invalid"] or any(f.kind in ("invalid_reference", "non_string_reference") for f in m.flags):
        return f"record 1 cites {m.stats['refs_invalid']} reference(s) that are not segment ids of its transcript"
    return None


def decide(recs):
    done = [i for i in ORDER if i in recs and recs[i].get("status") in ("parsed", "failed")]
    first3 = [i for i in ORDER[:3] if i in done]
    why = []
    if "00168" in done:
        p = r1_problem(recs)
        if p:
            why.append("R1: " + p)
    caps = [i for i in first3 if recs[i].get("finish_reason") == "length"]
    if len(caps) >= 2:
        why.append(f"R2: two of the first three records reached the token cap: {caps}")
    if caps:
        high = [i for i in first3 if i not in caps and (recs[i].get("completion_tokens") or 0) > HIGH]
        if high:
            why.append(f"R3: {caps} reached the cap while {high} exceeded {HIGH} tokens")
    return done, first3, why


def main():
    started = time.time()
    seen = -1
    while True:
        pids = runner_pids()
        recs = {}
        if MAN.exists():
            try:
                recs = json.loads(MAN.read_text(encoding="utf-8-sig"))["records"]
            except Exception:                                      # noqa: BLE001  (manifest being rewritten)
                recs = {}
        done, first3, why = decide(recs)
        if len(done) != seen:
            seen = len(done)
            with LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"time": time.ctime(), "completed_records": done, "tokens": {i: recs[i].get("completion_tokens") for i in done},
                                    "finish": {i: recs[i].get("finish_reason") for i in done}, "triggered": why}) + "\n")
        if why:
            for p in pids:
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {p} -Force"], capture_output=True)
            RESULT.write_text(json.dumps({"stopped_by_rule": True, "reasons": why, "completed_records": done, "terminated_pids": pids, "time": time.ctime()}, indent=1), encoding="utf-8")
            return
        if not pids and time.time() - started > 180:
            RESULT.write_text(json.dumps({"stopped_by_rule": False, "reasons": [], "completed_records": done, "note": "runner no longer running; no stop rule triggered", "time": time.ctime()}, indent=1), encoding="utf-8")
            return
        time.sleep(15)


if __name__ == "__main__":
    main()
