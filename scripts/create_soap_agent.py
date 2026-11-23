#!/usr/bin/env python3
"""Create (or add a new version of) the SOAP prompt agent in the Microsoft Foundry project, with the instructions of prompts/soap_agent_instructions_v1.md.

  python scripts/create_soap_agent.py --dry-run                       # show what would be created, nothing is sent
  python scripts/create_soap_agent.py --model <deployment name> --update-env   # create the agent version (needs `az login`) and write SOAP_AGENT_VERSION into .env
  options: --name clinical-soap-note   --instructions prompts/soap_agent_instructions_v1.md

Uses FOUNDRY_PROJECT_ENDPOINT from .env and your Azure CLI sign-in (the same way the reconstruction stage connects). The model is the name of a deployment in
the project (for example the one in FOUNDRY_MODEL_DEPLOYMENT_NAME, or your gpt-5.x deployment). Afterwards set in .env:
  SOAP_BACKEND=agent   SOAP_AGENT_NAME=<name>   SOAP_AGENT_VERSION=<the version printed here; required>   (--update-env does this for you)
Creating a version is a change in your Azure project: run it yourself, or the portal route works too (Agents > New agent > paste the instructions)."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _set_env(path: Path, values: dict[str, str]) -> None:
    """Set or add the given keys in a .env file; every other line is kept exactly as it is."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    done: set[str] = set()
    for i, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if key in values and not line.lstrip().startswith("#"):
            lines[i] = f"{key}={values[key]}"
            done.add(key)
    lines += [f"{k}={v}" for k, v in values.items() if k not in done]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default=os.getenv("SOAP_AGENT_NAME", "").strip() or "clinical-soap-note")
    ap.add_argument("--model", default=os.getenv("SOAP_AGENT_MODEL", "").strip() or os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "").strip(), help="deployment name in the Foundry project")
    ap.add_argument("--instructions", default=str(ROOT / "prompts" / "soap_agent_instructions_v1.md"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--update-env", action="store_true", help="write SOAP_AGENT_NAME and SOAP_AGENT_VERSION into .env (only these two lines are touched)")
    a = ap.parse_args()

    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip().rstrip("/")
    text = Path(a.instructions).read_text(encoding="utf-8")
    print(f"project   : {urlparse(endpoint).netloc or '(FOUNDRY_PROJECT_ENDPOINT not set)'}")
    print(f"agent name: {a.name}")
    print(f"model     : {a.model or '(none: pass --model <deployment name>)'}")
    print(f"prompt    : {Path(a.instructions).name}, {len(text.split())} words, sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}")
    if a.dry_run:
        print("dry run: nothing was created.")
        return 0
    if not endpoint or not a.model:
        print("Set FOUNDRY_PROJECT_ENDPOINT in .env and pass --model <deployment name>.")
        return 2
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition
    from azure.identity import AzureCliCredential

    credential = AzureCliCredential()
    try:
        with AIProjectClient(endpoint=endpoint, credential=credential) as client:
            created = client.agents.create_version(agent_name=a.name, definition=PromptAgentDefinition(model=a.model, instructions=text),
                                                   description="Writes a US-style SOAP progress note from the clinical summary of an encounter.")
    finally:
        credential.close()
    print(f"created agent '{getattr(created, 'name', a.name)}' version {getattr(created, 'version', '?')}")
    version = str(getattr(created, "version", "") or "")
    if a.update_env and version:
        _set_env(ROOT / ".env", {"SOAP_AGENT_NAME": a.name, "SOAP_AGENT_VERSION": version})
        print(f"wrote SOAP_AGENT_NAME={a.name} and SOAP_AGENT_VERSION={version} to .env. Restart the backend.")
    else:
        print(f"next: set SOAP_AGENT_NAME={a.name} and SOAP_AGENT_VERSION={version} in .env, then restart the backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
