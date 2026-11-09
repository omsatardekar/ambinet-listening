#!/usr/bin/env python3
"""
ambient_tts.py - build synthetic multi-speaker clinical consultation audio.

Subcommands:
  voices    list English neural voices available to your Azure Speech resource
  generate  dialogue.txt -> raw audio.wav + dataset manifest
  validate  check WAV format, duration, counts, and manifest
  package   validate, then build ambient_clinical_audio_toolkit_dataset.zip

All speech is SYNTHETIC. Transcripts are GROUND TRUTH for the generated dialogue
(not ASR output), so they carry no confidence scores.
"""
from __future__ import annotations

import argparse, hashlib, json, logging, os, random, re, sys, time, wave, zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from scipy.signal import butter, lfilter

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

SR = 16000
MIN_BYTES = int(0.10 * SR * 2)          # reject synthesized turns shorter than 0.1 s
LOW_GAIN = 0.35                          # level for turns flagged '!' (mumbled / low confidence)
WORDS_PER_SEC = 2.4                      # used only by --dry-run estimate
ROOT_NAME = "clinical_audio_dataset"
log = logging.getLogger("ambient_tts")

LINE_RE = re.compile(r"^(?P<spk>[A-Z][A-Z0-9]*)(?P<flags>[~!]*)(?:\{(?P<opts>[^}]*)\})?:\s*(?P<text>.+?)\s*$")


# ----------------------------------------------------------------------------- parsing
def parse_dialogue(path: Path, speakers: dict) -> list[dict]:
    """Line format:  KEY[flags][{opts}]: text
       flags: '~' overlaps the end of the previous turn, '!' reduced-quality (quiet, muffled) speech
       opts : p=<sec> pause before turn, ov=<sec> overlap length (with '~')"""
    turns = []
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m:
            raise ValueError(f"{path}:{n}: cannot parse line: {line[:60]!r}")
        if m["spk"] not in speakers:
            raise ValueError(f"{path}:{n}: speaker key {m['spk']!r} not defined in scenario.json")
        opts = {}
        if m["opts"]:
            for kv in m["opts"].split(","):
                k, v = kv.split("=")
                opts[k.strip()] = float(v)
        turns.append(dict(key=m["spk"], text=m["text"], overlap="~" in m["flags"],
                          low="!" in m["flags"], opts=opts, line=n))
    if not turns:
        raise ValueError(f"{path}: no dialogue turns found")
    return turns


def resolve_speaker(sp: dict) -> dict:
    sp = dict(sp)
    sp["voice"] = os.environ.get(f"VOICE_{sp['role']}", sp["voice"])
    sp.setdefault("rate", "0%")
    sp.setdefault("pitch", "0%")
    return sp


# ----------------------------------------------------------------------------- engines
class FatalSynthError(RuntimeError):
    pass


class AzureEngine:
    name = "azure"

    def __init__(self, min_interval: float):
        try:
            import azure.cognitiveservices.speech as sdk
        except ImportError:
            raise SystemExit("Missing dependency: pip install -r requirements.txt")
        key, region = os.environ.get("AZURE_SPEECH_KEY"), os.environ.get("AZURE_SPEECH_REGION")
        if not key or not region:
            raise SystemExit("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in the project-root .env file.")
        self.sdk = sdk
        cfg = sdk.SpeechConfig(subscription=key, region=region)
        cfg.set_speech_synthesis_output_format(sdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm)
        self.synthesizer = sdk.SpeechSynthesizer(speech_config=cfg, audio_config=None)
        self.min_interval, self._last = min_interval, 0.0

    def synth(self, voice, rate, pitch, text) -> bytes:
        wait = self._last + self.min_interval - time.time()
        if wait > 0:
            time.sleep(wait)
        lang = "-".join(voice.split("-")[:2])
        ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{lang}">'
                f'<voice name="{voice}"><prosody rate="{rate}" pitch="{pitch}">{escape(text)}</prosody>'
                f'</voice></speak>')
        res = self.synthesizer.speak_ssml_async(ssml).get()
        self._last = time.time()
        if res.reason == self.sdk.ResultReason.SynthesizingAudioCompleted:
            return bytes(res.audio_data)
        detail = ""
        if res.reason == self.sdk.ResultReason.Canceled:
            c = self.sdk.SpeechSynthesisCancellationDetails(res)
            detail = f"{c.error_code.name}: {c.error_details}"
            if c.error_code.name in {"AuthenticationFailure", "BadRequestParameters"}:
                raise FatalSynthError(detail)
        raise RuntimeError(f"synthesis not completed ({res.reason}) {detail}")

    def list_voices(self):
        return self.synthesizer.get_voices_async("").get().voices


class FakeEngine:
    """TEST ONLY: tone 'speech' with syllable-like envelope. Proves the pipeline without Azure."""
    name = "fake"

    def synth(self, voice, rate, pitch, text) -> bytes:
        dur = max(0.4, len(text.split()) / 2.6)
        f0 = 90 + int(hashlib.md5(voice.encode()).hexdigest()[:4], 16) % 140
        t = np.arange(int(dur * SR)) / SR
        env = 0.5 * (1 + np.sin(2 * np.pi * 3.5 * t))
        sig = 0.3 * env * (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * 2 * f0 * t))
        return (sig * 32767).astype("<i2").tobytes()


def synth_turn(engine, voice, rate, pitch, text, cache: Path, retries=5):
    key = hashlib.sha1("|".join([engine.name, voice, rate, pitch, text]).encode()).hexdigest()
    f = cache / f"{key}.pcm"
    if f.exists() and f.stat().st_size >= MIN_BYTES:
        return f.read_bytes(), True
    last = None
    for attempt in range(1, retries + 1):
        try:
            data = engine.synth(voice, rate, pitch, text)
            if not data or len(data) < MIN_BYTES:
                raise RuntimeError("empty or too-short audio returned")
            f.write_bytes(data)
            return data, False
        except FatalSynthError:
            raise
        except Exception as e:                      # noqa: BLE001 - retry on anything transient
            last = e
            wait = min(30, 2 ** attempt) + random.random()
            log.warning("synth attempt %d/%d failed (%s); retrying in %.1fs", attempt, retries, e, wait)
            time.sleep(wait)
    raise RuntimeError(f"synthesis failed after {retries} attempts for {text[:50]!r}: {last}")


# ----------------------------------------------------------------------------- audio
def lowpass(x: np.ndarray) -> np.ndarray:
    b, a = butter(4, 1800 / (SR / 2))
    return lfilter(b, a, x).astype(np.float32)


def mmss(sec: float) -> str:
    return f"{int(sec // 60):02d}:{sec % 60:04.1f}"


def hms(sec: float) -> str:
    return f"{int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:{sec % 60:06.3f}"


def render(turns, pcms, seed, noise_db):
    rng = random.Random(seed)
    placed, cursor, prev_s, prev_e = [], int(0.6 * SR), 0, 0
    for i, (t, pcm) in enumerate(zip(turns, pcms)):
        x = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        if t["low"]:
            x = lowpass(x) * LOW_GAIN
        if i == 0:
            start = cursor
        elif t["overlap"]:
            start = max(prev_s, prev_e - int(t["opts"].get("ov", 0.5) * SR))
        else:
            start = cursor + int(t["opts"].get("p", rng.uniform(0.35, 0.95)) * SR)
        end = start + len(x)
        placed.append((start, end, x))
        cursor = max(cursor, end)
        prev_s, prev_e = start, end
    total = cursor + int(0.8 * SR)
    buf = np.zeros(total, dtype=np.float32)
    for s, e, x in placed:
        buf[s:e] += x
    buf += np.random.default_rng(seed).normal(0, 10 ** (noise_db / 20), total).astype(np.float32)  # room tone
    peak = float(np.max(np.abs(buf)))
    if peak > 0:
        buf *= 0.89 / peak
    return (buf * 32767).astype("<i2"), placed


def write_wav(path: Path, pcm: np.ndarray):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ----------------------------------------------------------------------------- generate
COMMON_LIMITS = [
    "Voices are synthetic text-to-speech; prosody, hesitations and room acoustics are far cleaner than real clinics.",
    "Transcript is ground truth for the generated dialogue, not ASR output, so no confidence scores are provided.",
    "Timestamps are exact turn-level offsets in the mixed WAV; word-level timestamps are NOT provided.",
    "Overlapping speech is simulated by mixing separately synthesized turns; real overlap is messier.",
    "Reduced-quality speech (flag reduced_audio_quality) is simulated with attenuation and low-pass filtering.",
    "Disfluencies are written into the text; the TTS engine may render some fillers more smoothly than a human would.",
]


def scenario_dirs(root: Path, only: str | None):
    ds = sorted(d for d in root.iterdir() if d.is_dir() and (d / "scenario.json").exists())
    return [d for d in ds if not only or only in d.name]


def cmd_generate(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dirs = scenario_dirs(Path(a.scenarios), a.only)
    if not dirs:
        raise SystemExit("No scenarios found.")
    if a.dry_run:
        print(f"{'encounter':<38}{'turns':>6}{'words':>7}{'chars':>8}{'est.min':>9}")
        tot = 0
        for d in dirs:
            sc = json.loads((d / "scenario.json").read_text())
            turns = parse_dialogue(d / "dialogue.txt", sc["speakers"])
            words = sum(len(t["text"].split()) for t in turns); chars = sum(len(t["text"]) for t in turns)
            est = (words / WORDS_PER_SEC + len(turns) * 0.65) / 60
            tot += chars
            print(f"{sc['encounter_id']:<38}{len(turns):>6}{words:>7}{chars:>8}{est:>9.1f}")
        print(f"Total billable characters (approx, Azure): {tot}. Estimates are +/-15%; real durations come from `generate`.")
        return
    engine = FakeEngine() if a.engine == "fake" else AzureEngine(float(os.environ.get("AZURE_TTS_MIN_INTERVAL_SEC", "0.1")))
    cache = Path(a.cache); cache.mkdir(exist_ok=True)
    manifests, billed = [], 0
    for d in dirs:
        sc = json.loads((d / "scenario.json").read_text())
        speakers = {k: resolve_speaker(v) for k, v in sc["speakers"].items()}
        turns = parse_dialogue(d / "dialogue.txt", speakers)
        log.info("== %s: %d turns", sc["encounter_id"], len(turns))
        pcms = []
        for i, t in enumerate(turns, 1):
            sp = speakers[t["key"]]
            data, cached = synth_turn(engine, sp["voice"], sp["rate"], sp["pitch"], t["text"], cache)
            billed += 0 if cached else len(t["text"])
            pcms.append(data)
            if i % 20 == 0:
                log.info("   %d/%d turns", i, len(turns))
        pcm, placed = render(turns, pcms, a.seed, a.noise_db)
        eo = out / d.name; eo.mkdir(exist_ok=True)
        write_wav(eo / "audio.wav", pcm)
        dur = len(pcm) / SR
        # Raw dataset contains audio only; no transcripts, speaker labels, or role mappings.
        man = {
            "encounter_id": sc["encounter_id"], "title": sc["title"],
            "audio_file": f"{d.name}/audio.wav", "audio_duration_sec": round(dur, 2),
            "audio_duration_mmss": mmss(dur), "meets_10_minute_target": dur >= 600,
            "difficulty": sc.get("difficulty", "unspecified"),
            "audio_format": {"container": "WAV", "encoding": "PCM signed 16-bit LE", "channels": 1, "sample_rate_hz": SR},
            "synthetic_data": True,
            "known_limitations": COMMON_LIMITS + sc.get("known_limitations", []),
            "generation": {"engine": engine.name, "seed": a.seed,
                           "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        }
        manifests.append(man)
        log.info("   wrote %s (%s)%s", eo / "audio.wav", mmss(dur), "" if dur >= 600 else "  ** SHORTER THAN 10 MIN **")
    (out / "dataset_manifest.json").write_text(json.dumps({"encounters": manifests}, indent=2), encoding="utf-8")
    (out / "README.md").write_text("# Synthetic clinical audio dataset\n\nWAV files only. This folder intentionally excludes dialogue text, transcripts, speaker-role mappings, and downstream outputs. All encounters are fictional synthetic speech.\n", encoding="utf-8")
    log.info("Done. Characters sent to the TTS service this run (cache misses): %d", billed)


# ----------------------------------------------------------------------------- validate
def validate_encounter(d: Path, min_min: float):
    checks = []
    def chk(name, ok, detail="", level="fail"):
        checks.append({"check": name, "status": "pass" if ok else level, "detail": detail})
    wav = d / "audio.wav"
    chk("audio.wav exists", wav.exists())
    if not wav.exists():
        return checks
    try:
        with wave.open(str(wav), "rb") as w:
            ch, sw, sr, nf = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            raw = w.readframes(nf)
    except Exception as e:
        chk("audio.wav readable", False, str(e)); return checks
    chk("format mono / 16-bit / 16 kHz PCM", (ch, sw, sr) == (1, 2, SR), f"channels={ch} width={sw} rate={sr}")
    dur = nf / sr if sr else 0
    chk(f"duration >= {min_min:g} min", dur >= min_min * 60, f"{mmss(dur)}", level="warn")
    chk("audio contains non-silent samples", bool(raw) and np.any(np.frombuffer(raw, dtype="<i2") != 0))
    return checks


def cmd_validate(a, quiet=False):
    out = Path(a.out)
    if not out.exists():
        raise SystemExit(f"Output directory does not exist: {out}")
    dirs = sorted(d for d in out.iterdir() if d.is_dir() and d.name.startswith("encounter_"))
    report, fails = {}, 0
    if len(dirs) != 50:
        report["_dataset"] = [{"check": "exactly 50 encounter directories", "status": "fail", "detail": f"found {len(dirs)}"}]
        fails += 1
    for d in dirs:
        checks = validate_encounter(d, a.min_minutes)
        report[d.name] = checks
        if not quiet:
            print(f"\n{d.name}")
            for c in checks:
                print(f"  [{c['status'].upper():4}] {c['check']}  {c['detail']}")
        fails += sum(c["status"] == "fail" for c in checks)
    manifest_path = out / "dataset_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = manifest.get("encounters", [])
            chk = {"check": "manifest count matches WAV folders", "status": "pass" if len(entries) == len(dirs) else "fail", "detail": f"manifest={len(entries)}, folders={len(dirs)}"}
            report["_manifest"] = [chk]
            fails += chk["status"] == "fail"
        except Exception as e:
            report["_manifest"] = [{"check": "manifest parses", "status": "fail", "detail": str(e)}]
            fails += 1
    else:
        report["_manifest"] = [{"check": "dataset_manifest.json exists", "status": "fail", "detail": "missing manifest"}]
        fails += 1
    (out / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    warns = sum(c["status"] == "warn" for v in report.values() for c in v)
    print(f"\nValidation: {fails} failure(s), {warns} warning(s). Report: {out / 'validation_report.json'}")
    return fails == 0


def cmd_package(a):
    if not cmd_validate(a, quiet=True) and not a.force:
        raise SystemExit("Validation failed; fix the output or re-run with --force.")
    out = Path(a.out)
    zp = Path(a.zip)
    zp.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in (out / "README.md", out / "dataset_manifest.json"):
            if f.exists(): z.write(f, f"{ROOT_NAME}/{f.name}")
        for d in sorted(out.glob("encounter_*")):
            wav = d / "audio.wav"
            if wav.exists(): z.write(wav, f"{ROOT_NAME}/{d.name}/audio.wav")
    print(f"Packaged raw WAV dataset: {zp} ({zp.stat().st_size / 1e6:.2f} MB)")


def cmd_voices(a):
    for v in AzureEngine(0).list_voices():
        if v.locale.startswith("en-"):
            print(f"{v.short_name:<34}{v.locale:<8}{v.gender.name}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--scenarios", default="scenarios"); g.add_argument("--out", default="output")
    g.add_argument("--engine", choices=["azure", "fake"], default="azure")
    g.add_argument("--only"); g.add_argument("--dry-run", action="store_true")
    g.add_argument("--seed", type=int, default=7); g.add_argument("--noise-db", type=float, default=-62)
    g.add_argument("--cache", default=".tts_cache")
    v = sub.add_parser("validate"); v.add_argument("--out", default="output/clinical_audio_dataset"); v.add_argument("--min-minutes", type=float, default=10)

    k = sub.add_parser("package")
    k.add_argument("--out", default="output/clinical_audio_dataset")
    k.add_argument("--min-minutes", type=float, default=10)
    k.add_argument("--zip", default="ambient_clinical_audio_toolkit_dataset.zip")
    k.add_argument("--force", action="store_true")
    a = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    {"generate": cmd_generate, "validate": lambda x: sys.exit(0 if cmd_validate(x) else 1),
     "package": cmd_package, "voices": cmd_voices}[a.cmd](a)


if __name__ == "__main__":
    main()
