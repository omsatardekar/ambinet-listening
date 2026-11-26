"""Connectivity check for both judges: sends ONE tiny synthetic prompt (no project or patient data) and reports PASS/FAIL. Prints no keys.

    python -m finetune_slm.evaluation.judge_eval.check_endpoints
"""
from __future__ import annotations

import json
import sys

from .client import Judge, JudgeError, parse_json_reply

SYSTEM = "You are a strict JSON-only responder."
USER = 'A synthetic test. Reply with exactly this JSON and nothing else: {"status": "ok", "sum": 7}. The sum is 3 + 4.'


def check(prefix: str) -> bool:
    judge = Judge(prefix)
    print(f"[{prefix}] {judge.describe()}")
    if not judge.configured():
        print(f"[{prefix}] FAIL: URL, key or deployment missing in .env")
        return False
    try:
        reply = judge.call(SYSTEM, USER, max_output_tokens=300, use_cache=False)
        data = parse_json_reply(reply.text)
    except JudgeError as exc:
        print(f"[{prefix}] FAIL: {exc.code}: {exc.message}")
        return False
    good = data.get("status") == "ok" and data.get("sum") == 7
    print(f"[{prefix}] {'PASS' if good else 'REPLIED BUT WRONG'}: reply={json.dumps(data)[:120]} usage={ {k: v for k, v in reply.usage.items() if isinstance(v, int)} }")
    return good


if __name__ == "__main__":
    results = [check("JUDGE"), check("JUDGE2")]
    sys.exit(0 if all(results) else 1)
