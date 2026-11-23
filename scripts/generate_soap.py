#!/usr/bin/env python3
"""Write the SOAP note of one encounter from the command line (the same code as the web app, no server needed).

  python scripts/generate_soap.py --extraction path\\to\\51extraction.json           # a saved extraction file (for example downloaded from the extraction container)
  python scripts/generate_soap.py --encounter 51                                   # read {NN}extraction.json from the extraction container
  python scripts/generate_soap.py --encounter 51 --save                            # ... and save {NN}soap.json / {NN}soap.md in the soap container
  python scripts/generate_soap.py --extraction x.json --dry-run                    # only show what would be sent (flags and passages), no model call
  options: --backend agent|model   --out folder (default soap_out)

Use synthetic data only until real data is approved: the extraction is sent to the agent or model you configured."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import os  # noqa: E402

from soap_generation import blob_io, config, llm, prepare  # noqa: E402
from soap_generation.service import make_note  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--extraction", help="a saved extraction JSON file ({extraction, evidence, ...})")
    src.add_argument("--encounter", help="recording number; the extraction is read from the extraction container")
    ap.add_argument("--backend", choices=["agent", "model"], help="override SOAP_BACKEND")
    ap.add_argument("--out", default="soap_out")
    ap.add_argument("--transcript", help="a compact transcript JSON ({segments: [...]}) to give the writer the whole conversation as well")
    ap.add_argument("--save", action="store_true", help="also upload the note to the soap container")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.backend:
        os.environ[config.ENV_BACKEND] = a.backend

    if a.extraction:
        doc = json.loads(Path(a.extraction).read_text(encoding="utf-8"))
        ref = str(doc.get("encounter_ref") or doc.get("encounter_id") or Path(a.extraction).stem.rstrip("extraction") or "0")
    else:
        doc, _ = blob_io.fetch_extraction(a.encounter)
        ref = a.encounter

    conversation = json.loads(Path(a.transcript).read_text(encoding="utf-8")).get("segments") if a.transcript else None
    payload = prepare.build_input(doc, conversation)
    n_items = sum(len(v) for v in payload["extraction"].values())
    print(f"encounter {payload['encounter']['encounter_id']}: {n_items} findings, {len(payload['source_passages'])} with linked passages, "
          f"{len(payload['data_quality_flags'])} rule flags")
    for f in payload["data_quality_flags"]:
        print(f"  flag {f['ref']}: {f['issue']}")
    if a.dry_run:
        return 0

    print(f"writing the note with backend '{config.backend()}' ...")
    try:
        result = make_note(doc, llm.generate, conversation=conversation)
    except llm.LlmError as exc:
        print(f"FAILED ({exc.code}): {exc.message}")
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    number = f"{int(''.join(c for c in ref if c.isdigit()) or 0):02d}"
    (out / f"{number}soap.json").write_text(json.dumps({"note": result["note"], "review": result["review"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / f"{number}soap.md").write_text(result["markdown"], encoding="utf-8")
    print(f"\n{result['markdown']}\n")
    print(f"values not traced to the conversation: {len(result['review']['system_checks'])}; items the writer asked to verify: {len(result['note']['clinician_review']['items_to_verify'])}")
    print(f"saved locally: {out / (number + 'soap.json')} and {out / (number + 'soap.md')}")
    if a.save:
        info = blob_io.save_note(ref, {"document_type": "soap_note", "version": 1, "encounter_id": payload["encounter"]["encounter_id"], "note": result["note"],
                                       "review": result["review"], "markdown": result["markdown"]}, result["markdown"])
        print(f"uploaded to container '{info['container']}': {info['blob_name']}, {info['markdown_blob']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
