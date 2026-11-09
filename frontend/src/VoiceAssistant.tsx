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
  recordings: Recording[];
  error: string | null;
};

type MeterUpdate = { type: "meter"; level: number; elapsed: number; audio_connected: boolean };

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

/* ─── Green level wave (canvas, driven by the live microphone level) ─── */
function VoiceWave({ level, active }: { level: number; active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const targetRef = useRef(0);
  const activeRef = useRef(active);

  useEffect(() => {
    targetRef.current = Math.min(1, Math.sqrt(Math.max(0, level)) * 1.5);
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

    const bars = 36;
    const gap = 3;
    const barWidth = (width - gap * (bars - 1)) / bars;
    const smooth = new Float32Array(bars);
    let smoothLevel = 0;
    let raf = 0;
    let t = 0;

    const draw = () => {
      t += 0.05;
      smoothLevel += (targetRef.current - smoothLevel) * 0.2;
      ctx.clearRect(0, 0, width, height);
      const center = (bars - 1) / 2;
      for (let i = 0; i < bars; i += 1) {
        const distance = Math.abs(i - center) / center;
        const shape = 1 - distance * 0.55;
        const idle = activeRef.current ? 0.08 + 0.05 * Math.sin(t * 1.3 + i * 0.4) : 0.04;
        const jitter = 0.55 + 0.45 * Math.abs(Math.sin(t * 2.6 + i * 1.7));
        const target = Math.min(1, idle + smoothLevel * shape * jitter);
        smooth[i] += (target - smooth[i]) * 0.35;
        const barHeight = Math.max(4, smooth[i] * height * 0.92);
        const x = i * (barWidth + gap);
        const y = (height - barHeight) / 2;
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        gradient.addColorStop(0, "rgba(72, 214, 160, 0.95)");
        gradient.addColorStop(1, "rgba(24, 150, 110, 0.85)");
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, barWidth / 2);
        ctx.fill();
      }
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
      offline: "Voice offline",
      loading: "Loading voice model",
      unavailable: "Voice unavailable",
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
                  : `Say "start recording" within ${Math.ceil(countdown)} seconds.`}
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
