import { useEffect, useRef, useState } from "react";
import "./VoiceAssistant.css";

/**
 * Hands-free voice control for the whole app.
 *
 *  - Always listening (when the workspace is up) — no panel, only a small status pill in the header.
 *  - "Hey Asha"            -> a Siri-style overlay opens and waits for a command.
 *  - "start recording"     -> recording starts immediately; the wave follows the microphone level.
 *  - "Hey Asha, stop recording" (or the Stop button) -> recording is saved and playable here.
 *
 * Audio is streamed to the local backend only. Nothing is uploaded from this component.
 */

export type VoiceStatus = { good: boolean; label: string };

type Recording = {
  session_id: string;
  started_at: string | null;
  duration_s: number;
  audio_url: string;
};

type SpeakerStatus = {
  available: boolean;
  loading: boolean;
  error: string | null;
  enrolled: boolean;
  enabled: boolean;
  active: boolean;
  threshold: number;
  enrolling: boolean;
  enroll_status: "idle" | "capturing" | "processing" | "done" | "failed";
  enroll_message: string | null;
  enroll_progress: number;
  enroll_target_seconds: number;
  last_score: number | null;
  last_ok: boolean | null;
  last_age: number | null;
};

type VoiceState = {
  type: "state";
  available: boolean;
  loading?: boolean;
  state: "listening" | "awake" | "recording" | "unavailable";
  current: { session_id: string; started_at: string | null } | null;
  level: number;
  audio_connected: boolean;
  input_silent?: boolean;
  stop_armed?: boolean;
  last_command: "wake" | "start" | "stop" | null;
  heard?: string;
  heard_age?: number | null;
  speaker?: SpeakerStatus | null;
  speaker_rejected_age?: number | null;
  recordings: Recording[];
  error: string | null;
};

type MeterUpdate = {
  type: "meter";
  level: number;
  elapsed: number;
  audio_connected: boolean;
  enroll_progress?: number;
  enrolling?: boolean;
};

type MicStatus = "requesting" | "ready" | "denied" | "unsupported" | "error";

type Mode = "offline" | "loading" | "unavailable" | "mic" | "waiting" | "idle" | "awake" | "recording";

const SAMPLE_RATE = 16000;
const FRAME_SAMPLES = 512;
const COMMAND_WINDOW_SECONDS = 10;

const INITIAL: VoiceState = {
  type: "state",
  available: false,
  state: "unavailable",
  current: null,
  level: 0,
  audio_connected: false,
  last_command: null,
  heard: "",
  heard_age: null,
  recordings: [],
  error: null,
};

function formatClock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(whole / 60)).padStart(2, "0")}:${String(whole % 60).padStart(2, "0")}`;
}

function formatWhen(value: string | null, fallback: string): string {
  if (!value) return fallback;
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? fallback
    : date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/* ─── Siri-style flowing wave (canvas, driven by the live microphone level) ─── */
const WAVE_LAYERS = [
  { color: "34, 211, 238", speed: 1.0, freq: 1.6, amp: 1.0, phase: 0 },
  { color: "139, 92, 246", speed: 1.35, freq: 2.2, amp: 0.8, phase: 1.7 },
  { color: "244, 114, 182", speed: 0.8, freq: 2.9, amp: 0.62, phase: 3.1 },
  { color: "52, 211, 153", speed: 1.7, freq: 1.2, amp: 0.5, phase: 4.6 },
];

function VoiceWave({ level, active }: { level: number; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const targetRef = useRef(0);
  const activeRef = useRef(active);

  useEffect(() => {
    targetRef.current = Math.min(1, Math.sqrt(Math.max(0, level)) * 1.6);
  }, [level]);
  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    let smoothLevel = 0;
    let raf = 0;
    let t = 0;

    const draw = () => {
      t += 0.035;
      smoothLevel += (targetRef.current - smoothLevel) * 0.18;
      const energy = (activeRef.current ? 0.14 : 0.05) + smoothLevel * 0.86;
      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = "lighter";
      const mid = height / 2;
      for (const layer of WAVE_LAYERS) {
        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, `rgba(${layer.color}, 0)`);
        gradient.addColorStop(0.5, `rgba(${layer.color}, 0.95)`);
        gradient.addColorStop(1, `rgba(${layer.color}, 0)`);
        ctx.beginPath();
        for (let x = 0; x <= width; x += 3) {
          const progress = x / width;
          const envelope = Math.pow(Math.sin(progress * Math.PI), 2.2);
          const y =
            mid +
            Math.sin(progress * Math.PI * 2 * layer.freq + t * layer.speed * 3 + layer.phase) *
              envelope * mid * 0.86 * energy * layer.amp;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.lineWidth = 2.4;
        ctx.strokeStyle = gradient;
        ctx.shadowColor = `rgba(${layer.color}, 0.9)`;
        ctx.shadowBlur = 14;
        ctx.stroke();
      }
      ctx.globalCompositeOperation = "source-over";
      ctx.shadowBlur = 0;
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  return <canvas ref={canvasRef} className="va-wave" aria-hidden="true" />;
}

/* ─── Main component ─── */
function VoiceAssistant({
  backendOnline,
  onStatusChange,
}: {
  backendOnline: boolean;
  onStatusChange: (status: VoiceStatus) => void;
}) {
  const [voice, setVoice] = useState<VoiceState>(INITIAL);
  const [mic, setMic] = useState<MicStatus>("requesting");
  const [micError, setMicError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [awakeSince, setAwakeSince] = useState<number | null>(null);
  const [savedClip, setSavedClip] = useState<Recording | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [lockOpen, setLockOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const wasRecording = useRef(false);

  // Ticker for countdowns and the recording clock
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, []);

  // ── State stream: initial snapshot, then live WebSocket updates ──
  useEffect(() => {
    let active = true;
    let reconnect = 0;
    let socket: WebSocket | null = null;

    const load = async () => {
      try {
        const response = await fetch("/api/wake/state");
        if (!response.ok) throw new Error("unavailable");
        const state = (await response.json()) as VoiceState;
        if (active) setVoice(state);
      } catch {
        if (active) setVoice((current) => ({ ...current, available: false }));
      }
    };

    const connect = () => {
      if (!active) return;
      const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
      const connection = new WebSocket(`${scheme}//${window.location.host}/api/wake/ws`);
      socket = connection;
      socketRef.current = connection;
      connection.onmessage = (message) => {
        const update = JSON.parse(message.data) as VoiceState | MeterUpdate;
        if (update.type === "meter") {
          setVoice((current) => ({
            ...current,
            level: update.level,
            audio_connected: update.audio_connected,
            speaker:
              current.speaker && update.enrolling
                ? { ...current.speaker, enrolling: true, enroll_progress: update.enroll_progress ?? 0 }
                : current.speaker,
          }));
        } else {
          setVoice(update);
        }
      };
      connection.onclose = () => {
        if (socketRef.current === connection) socketRef.current = null;
        if (active) reconnect = window.setTimeout(connect, 2000);
      };
      connection.onerror = () => connection.close();
    };

    void load();
    connect();
    return () => {
      active = false;
      window.clearTimeout(reconnect);
      socket?.close();
      socketRef.current = null;
    };
  }, []);

  // ── Microphone: 16 kHz mono, 512-sample frames streamed to the backend ──
  useEffect(() => {
    let active = true;
    let stream: MediaStream | null = null;
    let context: AudioContext | null = null;
    let processor: ScriptProcessorNode | null = null;
    let source: MediaStreamAudioSourceNode | null = null;
    let mute: GainNode | null = null;

    const capture = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setMic("unsupported");
        setMicError("Use Chrome or Edge on localhost to enable voice control.");
        return;
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: { channelCount: 1, echoCancellation: true, noiseSuppression: false, autoGainControl: true },
        });
        if (!active) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        try {
          context = new AudioContext({ sampleRate: SAMPLE_RATE });
        } catch {
          context = new AudioContext();
        }
        if (context.state === "suspended") await context.resume();
        if (!active) return;

        const inputRate = context.sampleRate;
        source = context.createMediaStreamSource(stream);
        // Small buffers keep microphone-to-server delay low (32 ms at 16 kHz, ~43 ms at 48 kHz).
        processor = context.createScriptProcessor(inputRate <= 16000 ? 512 : 2048, 1, 1);
        mute = context.createGain();
        mute.gain.value = 0;
        let pending = new Float32Array(0);
        let position = 0;
        let outgoing = new Int16Array(0);

        processor.onaudioprocess = (event) => {
          const input = event.inputBuffer.getChannelData(0);
          const merged = new Float32Array(pending.length + input.length);
          merged.set(pending);
          merged.set(input, pending.length);
          const ratio = inputRate / SAMPLE_RATE;
          const resampled: number[] = [];
          while (position + 1 < merged.length) {
            const left = Math.floor(position);
            const fraction = position - left;
            resampled.push(merged[left] + (merged[left + 1] - merged[left]) * fraction);
            position += ratio;
          }
          const consumed = Math.floor(position);
          pending = merged.slice(consumed);
          position -= consumed;

          const converted = new Int16Array(outgoing.length + resampled.length);
          converted.set(outgoing);
          for (let index = 0; index < resampled.length; index += 1) {
            const sample = Math.max(-1, Math.min(1, resampled[index]));
            converted[outgoing.length + index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
          }
          let offset = 0;
          while (converted.length - offset >= FRAME_SAMPLES) {
            const connection = socketRef.current;
            if (connection?.readyState === WebSocket.OPEN) {
              connection.send(converted.slice(offset, offset + FRAME_SAMPLES).buffer);
            }
            offset += FRAME_SAMPLES;
          }
          outgoing = converted.slice(offset);
        };

        source.connect(processor);
        processor.connect(mute);
        mute.connect(context.destination);
        setMic("ready");
        setMicError(null);
      } catch (error) {
        if (!active) return;
        const name = error instanceof DOMException ? error.name : "";
        setMic(name === "NotAllowedError" || name === "SecurityError" ? "denied" : "error");
        setMicError(error instanceof Error ? error.message : "The browser could not open the microphone.");
      }
    };

    void capture();
    return () => {
      active = false;
      if (processor) processor.onaudioprocess = null;
      source?.disconnect();
      processor?.disconnect();
      mute?.disconnect();
      stream?.getTracks().forEach((track) => track.stop());
      if (context && context.state !== "closed") void context.close();
    };
  }, []);

  // Countdown start: when the wake word is heard
  useEffect(() => {
    if (voice.state === "awake") setAwakeSince((current) => current ?? Date.now());
    else setAwakeSince(null);
  }, [voice.state]);

  // Keep the saved clip after a stop (from voice or button) so it can be played right away
  useEffect(() => {
    const recording = voice.state === "recording";
    if (recording) setSavedClip(null);
    if (wasRecording.current && !recording && voice.recordings[0]) setSavedClip(voice.recordings[0]);
    wasRecording.current = recording;
  }, [voice.state, voice.recordings]);

  // ── Derived state ──
  const audioFlowing = voice.audio_connected;
  const mode: Mode = !backendOnline
    ? "offline"
    : voice.loading
      ? "loading"
      : !voice.available
        ? "unavailable"
        : mic !== "ready"
          ? "mic"
          : !audioFlowing
            ? "waiting"
            : voice.state === "recording"
              ? "recording"
              : voice.state === "awake"
                ? "awake"
                : "idle";

  useEffect(() => {
    const labels: Record<Mode, string> = {
      offline: "Asha offline",
      loading: "Asha is getting ready",
      unavailable: "Asha unavailable",
      mic: mic === "denied" ? "Microphone blocked" : "Microphone needed",
      waiting: "Waiting for microphone",
      idle: 'Listening for "Hey Asha"',
      awake: "Listening for command",
      recording: "Recording",
    };
    const recentHeard = voice.heard && (voice.heard_age ?? 99) < 6;
    const suffix = recentHeard && mode !== "offline" ? ` · “${voice.heard!.slice(0, 40)}”` : "";
    onStatusChange({
      good: mode === "idle" || mode === "awake" || mode === "recording",
      label: labels[mode] + suffix,
    });
  }, [mode, mic, onStatusChange, voice.heard, voice.heard_age]);

  const countdown = awakeSince ? Math.max(0, COMMAND_WINDOW_SECONDS - (now - awakeSince) / 1000) : 0;
  const recordingSeconds = voice.current?.started_at
    ? Math.max(0, (now - new Date(voice.current.started_at).getTime()) / 1000)
    : 0;
  const heardFresh = Boolean(voice.heard) && voice.heard_age !== null && (voice.heard_age ?? 99) < 8;

  const overlayLive = mode === "awake" || mode === "recording";
  const overlaySaved = !overlayLive && savedClip !== null;
  const showOverlay = overlayLive || overlaySaved;
  const level = voice.level;

  const sendCommand = async (command: "start" | "stop") => {
    setBusy(true);
    setActionError(null);
    try {
      const response = await fetch(`/api/wake/recording/${command}`, { method: "POST" });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? "The recorder did not respond.");
      }
      setVoice((await response.json()) as VoiceState);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "The recorder did not respond.");
    } finally {
      setBusy(false);
    }
  };

  const dismissSaved = () => setSavedClip(null);

  const speaker = voice.speaker ?? null;
  const callSpeaker = async (path: string, init: RequestInit) => {
    setBusy(true);
    setActionError(null);
    try {
      const response = await fetch(`/api/speaker/${path}`, init);
      const body = (await response.json().catch(() => null)) as (SpeakerStatus & { detail?: string }) | null;
      if (!response.ok) throw new Error(body?.detail ?? "The speaker service did not respond.");
      if (body) setVoice((current) => ({ ...current, speaker: body }));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "The speaker service did not respond.");
    } finally {
      setBusy(false);
    }
  };
  const post = (body: unknown): RequestInit => ({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const lockLabel = !speaker
    ? "Voice lock"
    : speaker.active
      ? "Voice lock: on"
      : speaker.enrolled
        ? "Voice lock: off"
        : "Set up voice lock";
  const rejectedRecently = (voice.speaker_rejected_age ?? 99) < 6;

  return (
    <>
      {showOverlay && (
        <div className="va-stage">
        <section
          className={`va-overlay ${overlayLive ? `va-${mode}` : "va-saved"}`}
          aria-live="polite"
          aria-label="Voice recorder"
        >
          {overlayLive && (
            <>
              <div className="va-head">
                <span className="va-dot" />
                <span className="va-kicker">
                  {mode === "recording" ? "Recording" : "Hey Asha"}
                </span>
                {mode === "recording" && <span className="va-timer">{formatClock(recordingSeconds)}</span>}
              </div>
              <VoiceWave level={level} active />
              <p className="va-title">
                {mode === "recording" ? "Capturing the conversation" : "Asha is listening"}
              </p>
              <p className="va-sub">
                {mode === "recording"
                  ? voice.stop_armed
                    ? 'Asha is listening — say "stop recording".'
                    : 'Say "Hey Asha, stop recording" to save.'
                  : `Say "Start recording" — I'm listening for ${Math.ceil(countdown)}s.`}
              </p>
              {mode === "awake" && (
                <div className="va-countdown" aria-hidden="true">
                  <span style={{ width: `${(countdown / COMMAND_WINDOW_SECONDS) * 100}%` }} />
                </div>
              )}
              <div className="va-footer">
                <span className={`va-heard ${heardFresh ? "" : "va-heard-old"}`}>
                  {voice.heard ? `Heard “${voice.heard}”` : "Listening…"}
                </span>
                {mode === "recording" && (
                  <button type="button" className="va-btn" onClick={() => void sendCommand("stop")} disabled={busy}>
                    Stop and save
                  </button>
                )}
              </div>
              {actionError && <p className="va-error" role="alert">{actionError}</p>}
            </>
          )}

          {overlaySaved && savedClip && (
            <>
              <div className="va-head">
                <span className="va-dot va-dot-saved" />
                <span className="va-kicker">Saved</span>
                <span className="va-timer">{formatClock(savedClip.duration_s)}</span>
                <button type="button" className="va-close" onClick={dismissSaved} aria-label="Close">
                  ×
                </button>
              </div>
              <p className="va-title">Recording saved</p>
              <p className="va-sub">{formatWhen(savedClip.started_at, savedClip.session_id)} · WAV on this device</p>
              <audio controls preload="metadata" src={savedClip.audio_url} className="va-audio" />
              <div className="va-footer">
                <a className="va-link" href={savedClip.audio_url} download={`${savedClip.session_id}.wav`}>
                  Download
                </a>
                <button type="button" className="va-btn va-btn-ghost" onClick={() => setDrawerOpen(true)}>
                  All recordings
                </button>
              </div>
            </>
          )}
        </section>
        </div>
      )}

      {speaker && !lockOpen && (
        <button
          type="button"
          className={`va-recordings-pill va-lock-pill ${speaker.active ? "va-lock-on" : ""}`}
          onClick={() => setLockOpen(true)}
        >
          {lockLabel}
          {rejectedRecently && <span className="va-lock-alert">other voice</span>}
        </button>
      )}

      {lockOpen && speaker && (
        <div className="va-drawer-scrim" onClick={() => setLockOpen(false)}>
          <aside
            className="va-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Voice lock"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="va-drawer-head">
              <div>
                <h3>Voice lock</h3>
                <p>Only your enrolled voice can say “Hey Asha”. Processed on this device, never uploaded.</p>
              </div>
              <button type="button" className="va-close" onClick={() => setLockOpen(false)} aria-label="Close">
                ×
              </button>
            </div>

            {!speaker.available && (
              <p className="va-sub">
                {speaker.loading
                  ? "Loading the voice model… (the first start downloads it once)"
                  : `Voice lock is unavailable${speaker.error ? `: ${speaker.error}` : "."} Voice commands still work for everyone.`}
              </p>
            )}

            {speaker.available && (
              <>
                <p className="va-sub">
                  Status:{" "}
                  <strong>
                    {speaker.enrolled
                      ? speaker.enabled
                        ? "your voice is enrolled and the lock is on"
                        : "your voice is enrolled, lock is off"
                      : "no voice enrolled yet"}
                  </strong>
                </p>

                {speaker.enroll_status === "capturing" || speaker.enrolling ? (
                  <div className="va-enroll">
                    <p className="va-title">Keep talking…</p>
                    <p className="va-sub">{speaker.enroll_message ?? "Speak naturally for about 15 seconds."}</p>
                    <div className="va-countdown">
                      <span style={{ width: `${Math.round(speaker.enroll_progress * 100)}%` }} />
                    </div>
                    <button
                      type="button"
                      className="va-btn va-btn-ghost va-btn-wide"
                      disabled={busy}
                      onClick={() => void callSpeaker("enroll/cancel", { method: "POST" })}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className="va-btn va-btn-wide"
                      disabled={busy || mic !== "ready"}
                      onClick={() => void callSpeaker("enroll/start", { method: "POST" })}
                    >
                      {speaker.enrolled ? "Re-enroll my voice" : "Enroll my voice"}
                    </button>
                    {mic !== "ready" && <p className="va-error">Allow the microphone first.</p>}
                    {speaker.enroll_status === "processing" && <p className="va-sub">{speaker.enroll_message}</p>}
                    {speaker.enroll_status === "done" && <p className="va-sub">{speaker.enroll_message}</p>}
                    {speaker.enroll_status === "failed" && <p className="va-error">{speaker.enroll_message}</p>}
                  </>
                )}

                {speaker.enrolled && !speaker.enrolling && (
                  <div className="va-lock-settings">
                    <label className="va-lock-row">
                      <input
                        type="checkbox"
                        checked={speaker.enabled}
                        disabled={busy}
                        onChange={(event) => void callSpeaker("settings", post({ enabled: event.target.checked }))}
                      />
                      <span>Only respond to my voice</span>
                    </label>
                    <label className="va-lock-row va-lock-col">
                      <span>
                        Strictness: <strong>{speaker.threshold.toFixed(2)}</strong>
                        <em> (higher = stricter; lower if Asha ignores you)</em>
                      </span>
                      <input
                        type="range"
                        min={0.1}
                        max={0.7}
                        step={0.05}
                        value={speaker.threshold}
                        disabled={busy}
                        onChange={(event) => void callSpeaker("settings", post({ threshold: Number(event.target.value) }))}
                      />
                    </label>
                    <p className="va-sub">
                      Last check:{" "}
                      {speaker.last_score === null
                        ? "none yet. Say “Hey Asha”."
                        : `score ${speaker.last_score.toFixed(2)} → ${speaker.last_ok ? "accepted" : "ignored"}`}
                    </p>
                    <button
                      type="button"
                      className="va-btn va-btn-ghost va-btn-wide"
                      disabled={busy}
                      onClick={() => void callSpeaker("voiceprint", { method: "DELETE" })}
                    >
                      Delete my voiceprint
                    </button>
                  </div>
                )}
              </>
            )}
            {actionError && <p className="va-error" role="alert">{actionError}</p>}
          </aside>
        </div>
      )}

      {voice.recordings.length > 0 && !drawerOpen && (
        <button type="button" className="va-recordings-pill" onClick={() => setDrawerOpen(true)}>
          Recordings <span>{voice.recordings.length}</span>
        </button>
      )}

      {drawerOpen && (
        <div className="va-drawer-scrim" onClick={() => setDrawerOpen(false)}>
          <aside
            className="va-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Saved recordings"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="va-drawer-head">
              <div>
                <h3>Saved recordings</h3>
                <p>Stored as WAV in offline_recordings/ · never uploaded</p>
              </div>
              <button type="button" className="va-close" onClick={() => setDrawerOpen(false)} aria-label="Close">
                ×
              </button>
            </div>
            <button
              type="button"
              className="va-btn va-btn-wide"
              onClick={() => void sendCommand("start")}
              disabled={busy || (mode !== "idle" && mode !== "awake")}
            >
              Start recording
            </button>
            {actionError && <p className="va-error" role="alert">{actionError}</p>}
            {voice.recordings.length === 0 ? (
              <p className="va-empty">No recordings yet. Say “Hey Asha”, then “start recording”.</p>
            ) : (
              <ul className="va-list">
                {voice.recordings.map((recording) => (
                  <li key={recording.session_id} className="va-item">
                    <div className="va-item-meta">
                      <strong>{formatWhen(recording.started_at, recording.session_id)}</strong>
                      <span>{formatClock(recording.duration_s)}</span>
                    </div>
                    <audio controls preload="metadata" src={recording.audio_url} className="va-audio" />
                    <a className="va-link" href={recording.audio_url} download={`${recording.session_id}.wav`}>
                      Download
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        </div>
      )}
    </>
  );
}

export default VoiceAssistant;
