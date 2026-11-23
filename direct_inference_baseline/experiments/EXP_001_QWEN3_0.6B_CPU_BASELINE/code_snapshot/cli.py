"""Command line entry point. Works from any directory:  python direct_inference_baseline/cli.py <command>"""
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from direct_inference_baseline.config import settings as S  # noqa: E402
from direct_inference_baseline.config.model_config import GenerationConfig  # noqa: E402


def make_client(provider: str, max_new_tokens: int):
    st = S.load_settings()
    cfg = GenerationConfig(max_new_tokens=max_new_tokens)
    if provider == "huggingface":
        from direct_inference_baseline.inference.huggingface_client import HuggingFaceClient
        return HuggingFaceClient(st.hf_model_id, st.hf_device, cfg)
    if provider == "foundry":
        from direct_inference_baseline.inference.foundry_client import FoundryClient
        return FoundryClient(st.foundry_endpoint, S.foundry_key(), st.foundry_deployment, st.foundry_api_version, st.request_timeout)
    raise SystemExit(f"unknown provider {provider!r}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="direct_inference_baseline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-config")
    sub.add_parser("verify-frozen")
    sub.add_parser("split")
    c = sub.add_parser("verify-connectivity")
    c.add_argument("--provider")
    for name in ("smoke", "run"):
        r = sub.add_parser(name)
        r.add_argument("--split", choices=["development", "test"], default="development")
        r.add_argument("--limit", type=int, default=None)
        r.add_argument("--ids", nargs="*")
        r.add_argument("--max-new-tokens", type=int, default=GenerationConfig().max_new_tokens)
        r.add_argument("--provider")
        r.add_argument("--experiment-id")
        r.add_argument("--i-approve-locked-test", action="store_true", help="required for --split test")
    e = sub.add_parser("evaluate")
    e.add_argument("--experiment-id", required=True)
    e.add_argument("--split", choices=["development", "test"], default=None)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(),
                        logging.FileHandler(S.LOG_DIR / "direct_inference.log", encoding="utf-8")])

    if a.cmd == "check-config":
        print(json.dumps(S.check_config(), indent=1))
    elif a.cmd == "verify-frozen":
        print(json.dumps(S.verify_frozen_dataset(), indent=1))
    elif a.cmd == "split":
        from direct_inference_baseline.evaluation.dataset_split import create_split
        m = create_split()
        print(json.dumps({k: m[k] for k in ("seed", "n_development", "n_test", "reproducible", "no_overlap", "all_ids_accounted_for")}, indent=1))
    elif a.cmd == "verify-connectivity":
        prov = a.provider or S.load_settings().provider
        cl = make_client(prov, 16)
        if prov == "huggingface":
            res = cl.generate("Reply with the single word: ready", 16)
            print(json.dumps({"provider": prov, "model": cl.describe(), "sample": res.text[:80], "finish": res.finish_reason,
                              "tokens_per_second": round((res.completion_tokens or 0) / res.latency_seconds, 2)}, indent=1))
        else:
            import requests
            st = S.load_settings()
            r = requests.get(f"{st.foundry_endpoint.rstrip('/')}/deployments?api-version={st.foundry_api_version}", headers={"api-key": S.foundry_key()}, timeout=30)
            names = [d.get("name") for d in r.json().get("value", [])] if r.ok else []
            print(json.dumps({"provider": "foundry", "http": r.status_code, "deployments": names, "qwen_available": any("qwen" in (n or "").lower() for n in names)}, indent=1))
    elif a.cmd in ("smoke", "run"):
        from direct_inference_baseline.evaluation.dataset_split import load_split
        from direct_inference_baseline.inference.inference_runner import run_inference
        if a.split == "test" and not a.i_approve_locked_test:
            raise SystemExit("The locked test split needs --i-approve-locked-test (explicit approval of the full run).")
        ids = a.ids or load_split(a.split)
        if a.limit:
            ids = ids[:a.limit]
        prov = a.provider or S.load_settings().provider
        cl = make_client(prov, a.max_new_tokens)
        m = run_inference(cl, ids, a.split, a.max_new_tokens, a.experiment_id)
        recs = m["records"].values()
        print(json.dumps({"experiment_id": m["experiment_id"], "records": len(m["records"]), "parsed": sum(r["status"] == "parsed" for r in recs),
                          "failed": sum(r["status"] == "failed" for r in recs)}, indent=1))
    elif a.cmd == "evaluate":
        from direct_inference_baseline.evaluation.evaluation_runner import evaluate_experiment
        out = evaluate_experiment(a.experiment_id)
        print(json.dumps(out["headline"], indent=1))


if __name__ == "__main__":
    main()
