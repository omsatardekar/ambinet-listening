"""Turn the 20 hand-written Module 3 scenarios (scenarios/*/dialogue.txt + scenario.json) into model inputs in the TRAINED format:
the short prompt + one line per segment `[SEG0001] person_1 (DOCTOR): text` (no timestamps).

  python finetune_slm/scripts/local/build_module3_eval.py --out finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl

These dialogues are natural, hand-written (not template generated) and were never used in training. There is no label file: the scenario.json
`design` block lists what was put in on purpose (facts, partial or uncertain items, what is absent) and is used to judge the extraction.
Limitation: this is the CLEAN text of the dialogue, not an ASR transcript of the audio, so it does not include speech recognition errors.
"""
import argparse, glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
p = argparse.ArgumentParser()
p.add_argument("--scenarios", default=os.path.join(ROOT, "scenarios"))
p.add_argument("--prompt", default=os.path.join(ROOT, "finetune_slm/data/round1_synthetic", "prompt", "short_prompt.txt"))
p.add_argument("--out", required=True)
a = p.parse_args()

template = open(a.prompt, encoding="utf-8").read()
LINE = re.compile(r"^([A-Z])([!~]?(?:\{[^}]*\})*[!~]?):\s*(.*)$")   # speaker tag, optional markers (!, ~{ov=..}, {p=..}), then the text
rows = []
for d in sorted(glob.glob(os.path.join(a.scenarios, "encounter_m3_*"))):
    sc = json.load(open(os.path.join(d, "scenario.json"), encoding="utf-8"))
    roles = {k: v["role"] for k, v in sc["speakers"].items()}
    order, lines = {}, []
    for raw in open(os.path.join(d, "dialogue.txt"), encoding="utf-8").read().splitlines():
        raw = raw.strip()
        if not raw: continue
        m = LINE.match(raw)
        if not m: raise SystemExit(f"unparsed line in {d}: {raw[:80]}")
        tag, text = m.group(1), re.sub(r"\{[^}]*\}", "", m.group(3)).strip()
        if not text: continue
        if tag not in order: order[tag] = f"person_{len(order) + 1}"
        lines.append(f"[SEG{len(lines) + 1:04d}] {order[tag]} ({roles.get(tag, 'UNKNOWN')}): {text}")
    eid = os.path.basename(d).replace("encounter_", "")
    user = template.replace("{ENCOUNTER_ID}", eid).replace("{TRANSCRIPT}", "\n".join(lines))
    rows.append({"id": eid, "source_batch": "module3_recordings", "split": "module3_recordings", "scenario_group": sc.get("title", ""),
                 "messages": [{"role": "user", "content": user}, {"role": "assistant", "content": json.dumps({"encounter_id": eid})}]})
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
print(len(rows), "encounters ->", a.out)
for r in rows[:3]:
    print(r["id"], len(r["messages"][0]["content"]), "chars;", r["messages"][0]["content"].count("[SEG"), "segments")
