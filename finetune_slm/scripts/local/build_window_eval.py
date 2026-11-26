"""Build the window records for the chunking experiment from the Module 3 recordings file.

  python finetune_slm/scripts/local/build_window_eval.py --in finetune_slm/data/module3_eval_inputs/module3_recordings.jsonl --out finetune_slm/data/module3_eval_inputs/module3_windows.jsonl --max_chars 7000
Each window becomes one record `<id>__w<k>` in the same format as the other evaluation files (local ids SEG0001..). windows_index.json keeps the window definitions for merging.
"""
import argparse, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from finetune_slm.scripts.shared.chunking import make_windows
LINE = re.compile(r"^\[(SEG\d{4})\] (person_\d+) \(([A-Z_]+)\): (.*)$")
ap = argparse.ArgumentParser()
ap.add_argument("--in", dest="inp", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--max_chars", type=int, default=7000)
ap.add_argument("--overlap", type=int, default=4)
a = ap.parse_args()
recs, index = [], {}
for line in open(a.inp, encoding="utf-8"):
    r = json.loads(line)
    user = r["messages"][0]["content"]
    head, tail = user.split("\n[SEG0001]", 1) if "\n[SEG0001]" in user else (None, None)
    assert head is not None, r["id"]
    segs = [dict(zip(("segment_id", "speaker_id", "role", "text"), m.groups())) for l in ("[SEG0001]" + tail).splitlines() if (m := LINE.match(l))]
    ws = make_windows(segs, a.max_chars, a.overlap)
    index[r["id"]] = [{"to_global": w["to_global"], "n": len(w["segments"])} for w in ws]
    for k, w in enumerate(ws, 1):
        tr = "\n".join(f"[{s['segment_id']}] {s['speaker_id']} ({s['role']}): {s['text']}" for s in w["segments"])
        new_user = head + "\n" + tr
        recs.append({**r, "id": f"{r['id']}__w{k}", "messages": [{"role": "user", "content": new_user}, r["messages"][1]]})
open(a.out, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in recs) + "\n")
json.dump(index, open(a.out.replace(".jsonl", "_index.json"), "w"), indent=1)
print(len(recs), "windows from", len(index), "encounters;", {k: len(v) for k, v in list(index.items())[:20]})
