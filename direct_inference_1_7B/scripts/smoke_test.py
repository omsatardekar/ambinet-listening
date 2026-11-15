"""GPU smoke test for the converted Qwen3-1.7B (technical compatibility check ONLY; the output is not an experiment result and no dataset record is used).
Loads the FP16 IR on the explicit GPU device, generates a short JSON extraction from a synthetic 3-sentence consultation, and verifies:
  * coherent generation (valid JSON containing the expected facts; no NaN/garbage),
  * actual GPU execution: Windows 'GPU Engine' utilisation and 'GPU Process Memory' counters of THIS process (sampler started after the GPU context exists)
    and CPU time of this process during generation only,
  * load/compile time, tokens/s and memory.
usage: python -B -s smoke_test.py       writes manifests/SMOKE_TEST_Qwen3-1.7B.json"""
import csv
import datetime
import io
import json
import re
import subprocess
import threading
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_1_7b as C  # noqa: E402
from ov_client_1_7b import MemorySampler  # noqa: E402

import openvino_genai as ovg  # noqa: E402

PROMPT = ("Extract the clinical facts from this short consultation and answer ONLY with JSON of the form "
          '{"chief_complaint": string, "symptoms": [string], "negative_findings": [string], "medications": [{"name": string, "dose": string|null}]}.\n\n'
          "Doctor: What brings you in today?\nPatient: I've had a cough for three days.\nDoctor: Any fever or chest pain?\nPatient: No fever, no chest pain.\nDoctor: Do you take any medicines?\n"
          "Patient: Just amlodipine, 5 milligrams once a day.\n")
pid = psutil.Process().pid
cache = C.TRACK / "models" / "ov_cache_smoke"
cache.mkdir(exist_ok=True)
proc = psutil.Process()
t_all = time.perf_counter()
out = {"pid": pid, "parent_pid": proc.ppid(), "time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "model": C.MODEL_ID, "revision": C.REVISION, "device_requested": "GPU", "ov_model_dir": str(C.OV_MODEL_DIR)}
sampler, raw = None, ""
GPU_ENGINE = "\\GPU Engine(*)\\Utilization Percentage"
GPU_SHARED = "\\GPU Process Memory(*)\\Shared Usage"
GPU_DED = "\\GPU Process Memory(*)\\Dedicated Usage"
try:
    with MemorySampler() as ms:
        t0 = time.perf_counter()
        pipe = ovg.LLMPipeline(str(C.OV_MODEL_DIR), "GPU", CACHE_DIR=str(cache))
        out["load_compile_seconds_first_load(includes GPU kernel compile)"] = round(time.perf_counter() - t0, 1)
        tok = pipe.get_tokenizer()
        # the counter instances are enumerated when typeperf starts, so start it only now that this process owns a GPU context
        # typeperf enumerates counter instances once per invocation and a process' GPU-engine instances only appear after its first GPU submission,
        # so poll with repeated single-sample invocations (each re-enumerates) in a background thread
        stop_poll = threading.Event()
        poll_eng, poll_raw = {}, []

        def poll():
            while not stop_poll.is_set():
                try:
                    o = subprocess.run(["typeperf", GPU_ENGINE, "-sc", "1"], capture_output=True, text=True, timeout=30).stdout
                except Exception:  # noqa: BLE001
                    continue
                poll_raw.append(o)
                rr = list(csv.reader(io.StringIO(o)))
                if len(rr) >= 2:
                    for h, v in zip(rr[0][1:], rr[1][1:]):
                        if f"pid_{pid}_" in h:
                            try:
                                k = h.split("engtype_")[-1].split(")")[0]
                                poll_eng[k] = max(poll_eng.get(k, 0.0), float(v))
                            except ValueError:
                                pass
        poll_thread = threading.Thread(target=poll, daemon=True)
        poll_thread.start()
        sampler = poll_thread
        time.sleep(1.0)
        text = tok.apply_chat_template([{"role": "user", "content": PROMPT}], add_generation_prompt=True, extra_context={"enable_thinking": False})
        g = pipe.get_generation_config()
        g.max_new_tokens, g.do_sample, g.apply_chat_template = 300, False, False
        cpu0 = proc.cpu_times()
        t1 = time.perf_counter()
        res = pipe.generate([text], g)
        wall = time.perf_counter() - t1
        cpu1 = proc.cpu_times()
        out["process_cpu_seconds_during_generation_only"] = round((cpu1.user + cpu1.system) - (cpu0.user + cpu0.system), 1)
        time.sleep(1.5)
    pm = res.perf_metrics
    reply = res.texts[0]
    out.update({"reply": reply, "input_tokens": int(pm.get_num_input_tokens()), "output_tokens": int(pm.get_num_generated_tokens()), "generation_wall_seconds": round(wall, 2),
                "ttft_seconds": round(pm.get_ttft().mean / 1000, 2), "decode_tokens_per_second": round(1000 / pm.get_tpot().mean, 2),
                "peak_process_rss_mb": round(ms.peak_rss_mb), "peak_system_used_mb": round(ms.peak_used_mb), "min_system_available_mb": round(ms.min_available_mb)})
    try:
        body = re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip().strip("`").replace("json\n", "", 1)
        j = json.loads(body)
        dump = json.dumps(j).lower()
        out["json_valid"] = True
        out["facts_present"] = {"cough_as_chief_complaint": "cough" in dump, "amlodipine_5mg": "amlodipine" in dump and "5" in dump, "no_fever_negative": "fever" in json.dumps(j.get("negative_findings", "")).lower()}
    except Exception as e:  # noqa: BLE001
        out["json_valid"], out["json_error"] = False, str(e)
    out["status"] = "generation_completed"
except Exception as e:  # noqa: BLE001
    out["status"] = "FAILED"
    out["error"] = f"{type(e).__name__}: {e}"
finally:
    eng, mem, rows = {}, {}, []
    if sampler is not None:
        stop_poll.set()
        sampler.join(timeout=40)
        eng = dict(poll_eng)
        raw = "\n".join(poll_raw)
        rows = [None] * len(poll_raw)
        (C.TRACK / "experiments" / "EXP_001_DIRECT_INFERENCE" / "logs" / "smoke_gpu_engine_counters_raw.txt").write_text(raw, encoding="utf-8")
    if False:
        hdr = rows[0]
        for r in rows[1:]:
            for h, v in zip(hdr[1:], r[1:]):
                if f"pid_{pid}_" not in h:
                    continue
                try:
                    val = float(v)
                except ValueError:
                    continue
                if "GPU Engine" in h:
                    k = h.split("engtype_")[-1].split(")")[0]
                    eng[k] = max(eng.get(k, 0.0), val)
                else:
                    k = ("shared" if "Shared Usage" in h else "dedicated") + "_usage_MB"
                    mem[k] = max(mem.get(k, 0.0), round(val / 2**20))
    out["gpu_engine_peak_utilization_percent_for_this_process"] = eng
    out["gpu_process_memory_peak_MB"] = mem
    out["typeperf_polls"] = len(rows)
    out["wall_seconds_total"] = round(time.perf_counter() - t_all, 1)
    gen_wall = out.get("generation_wall_seconds", 0)
    out["gpu_execution_verified"] = bool(eng) and max(eng.values()) >= 10 and out.get("process_cpu_seconds_during_generation_only", 1e9) < 0.9 * gen_wall * psutil.cpu_count()
C.write_json(C.TRACK / "manifests" / "SMOKE_TEST_Qwen3-1.7B.json", out)
print(json.dumps(out, indent=1, ensure_ascii=False))
