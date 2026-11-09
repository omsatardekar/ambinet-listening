import { ChangeEvent, DragEvent, ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, animate, motion, type Variants } from "framer-motion";
import {
  Activity, ArrowRight, AudioLines, Check, ClipboardList, FileText, Info, Mic, Play, RotateCcw,
  ShieldCheck, Sparkles, Stethoscope, TriangleAlert, UploadCloud, Users,
} from "lucide-react";
import VoiceAssistant, { type VoiceStatus } from "./VoiceAssistant";

type StageKey =
  | "audio_upload"
  | "speech_transcription"
  | "llm_reconstruction"
  | "final_transcript";

type StageStatus = "waiting" | "in_progress" | "completed" | "failed";
type SpeechProvider = "azure_speech" | "foundry_fast";
type SpeechProviderAvailability = {
  label: string;
  configured: boolean;
};

type StageState = {
  label: string;
  status: StageStatus;
  message: string;
};

type ProgressEvent = {
  sequence: number;
  run_id: string;
  filename: string;
  stage: StageKey | null;
  status: string;
  run_status: string;
  message: string;
  operation: string;
  percent: number;
  stages: Record<StageKey, StageState>;
  timestamp: string;
};

type TranscriptUtterance = {
  utterance_id?: string;
  start_seconds?: number | null;
  end_seconds?: number | null;
  duration_seconds?: number | null;
  canonical_speaker_id?: string;
  role?: string;
  text?: string;
  attribution_status?: string;
  attribution_confidence?: number;
};

type Speaker = {
  canonical_speaker_id?: string;
  role?: string;
  name?: string;
  display_name?: string;
  review_required?: boolean;
  attribution_status?: string;
};

type FinalTranscript = {
  processing_status?: string;
  processing_notice?: string;
  encounter_id?: string;
  utterances?: TranscriptUtterance[];
  speaker_registry?: Speaker[];
  review_flags?: unknown[];
};

type StartResponse = {
  run_id: string;
  events_url: string;
  status: string;
  speech_provider: SpeechProvider;
};

const STAGE_ORDER: StageKey[] = [
  "audio_upload",
  "speech_transcription",
  "llm_reconstruction",
  "final_transcript",
];

const INITIAL_STAGES: Record<StageKey, StageState> = {
  audio_upload: { label: "Recording received", status: "waiting", message: "Waiting" },
  speech_transcription: { label: "Speech transcription", status: "waiting", message: "Waiting" },
  llm_reconstruction: { label: "Conversation structure", status: "waiting", message: "Waiting" },
  final_transcript: { label: "Review-ready draft", status: "waiting", message: "Waiting" },
};

const ROLE_STYLES: Record<string, string> = {
  DOCTOR: "bg-cyan-400/10 text-cyan-200 ring-cyan-400/30",
  PATIENT: "bg-violet-400/10 text-violet-200 ring-violet-400/30",
  NURSE: "bg-emerald-400/10 text-emerald-200 ring-emerald-400/30",
  CAREGIVER: "bg-amber-400/10 text-amber-200 ring-amber-400/30",
  FAMILY_MEMBER: "bg-orange-400/10 text-orange-200 ring-orange-400/30",
  PHARMACIST: "bg-sky-400/10 text-sky-200 ring-sky-400/30",
  UNKNOWN: "bg-slate-400/10 text-slate-300 ring-slate-400/30",
};

const SPEECH_PROVIDER_OPTIONS: Array<{
  id: SpeechProvider;
  title: string;
  subtitle: string;
  description: string;
}> = [
  {
    id: "azure_speech",
    title: "Standard transcription",
    subtitle: "Full recording review",
    description: "Transcription with speaker separation for clinical review.",
  },
  {
    id: "foundry_fast",
    title: "Enhanced transcription",
    subtitle: "Alternative review",
    description: "An additional transcription route with speaker separation.",
  },
];

function clientProgressMessage(event: ProgressEvent): string {
  if (event.status === "failed") {
    return "This step could not be completed. Please contact your administrator.";
  }
  const step = (event.stage ? event.stages[event.stage]?.label : null) ?? "Workflow";
  return event.status === "completed" ? `${step} completed.` : `${step} in progress.`;
}

function App() {
  const fileInput = useRef<HTMLInputElement>(null);
  const eventSource = useRef<EventSource | null>(null);
  const transcriptPanel = useRef<HTMLDivElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [audioDuration, setAudioDuration] = useState<number | null>(null);
  const [dragging, setDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState("idle");
  const [currentStage, setCurrentStage] = useState<StageKey | null>(null);
  const [stages, setStages] = useState(INITIAL_STAGES);
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [percent, setPercent] = useState(0);
  const [currentOperation, setCurrentOperation] = useState("Select a recording to begin.");
  const [transcript, setTranscript] = useState<FinalTranscript | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [backendOnline, setBackendOnline] = useState(false);
  const [azureConfigured, setAzureConfigured] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>({ good: false, label: "Starting voice" });
  const [speechProvider, setSpeechProvider] = useState<SpeechProvider>("azure_speech");
  const [speechProviders, setSpeechProviders] = useState<
    Partial<Record<SpeechProvider, SpeechProviderAvailability>>
  >({});
  const [backendError, setBackendError] = useState<string | null>(null);
  const [streamReconnecting, setStreamReconnecting] = useState(false);

  const processing = runStatus === "queued" || runStatus === "running";
  const selectedProviderConfigured = Boolean(speechProviders[speechProvider]?.configured);

  useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      try {
        const response = await fetch("/api/health");
        if (!response.ok) throw new Error("Health check failed");
        const health = await response.json();
        if (active) {
          setBackendOnline(true);
          setAzureConfigured(Boolean(health.azure_configured));
          const providers = health.speech_providers ?? {};
          setSpeechProviders(providers);
          if (!providers[speechProvider]?.configured) {
            const availableProvider = SPEECH_PROVIDER_OPTIONS.find(
              (option) => providers[option.id]?.configured,
            );
            if (availableProvider) setSpeechProvider(availableProvider.id);
          }
        }
      } catch {
        if (active) {
          setBackendOnline(false);
          setAzureConfigured(false);
        }
      }
    };
    void checkHealth();
    const timer = window.setInterval(checkHealth, 30000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [speechProvider]);

  useEffect(() => {
    if (!selectedFile) {
      setAudioDuration(null);
      return;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    const audio = new Audio(objectUrl);
    audio.preload = "metadata";
    audio.onloadedmetadata = () => {
      if (Number.isFinite(audio.duration)) setAudioDuration(audio.duration);
    };
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  useEffect(() => {
    if (!startedAt || !processing) return;
    const updateElapsed = () => setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    updateElapsed();
    const timer = window.setInterval(updateElapsed, 1000);
    return () => window.clearInterval(timer);
  }, [startedAt, processing]);

  useEffect(() => {
    if (transcript && transcriptPanel.current) {
      transcriptPanel.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [transcript]);

  useEffect(() => () => eventSource.current?.close(), []);

  const chooseFile = (file?: File) => {
    if (!file) return;
    setUploadError(null);
    setBackendError(null);
    setTranscript(null);
    if (!file.name.toLowerCase().endsWith(".wav")) {
      setSelectedFile(null);
      setUploadError("Please choose a WAV recording.");
      return;
    }
    setSelectedFile(file);
  };

  const handleFileInput = (event: ChangeEvent<HTMLInputElement>) => {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  };

  const loadFinalResult = useCallback(async (id: string) => {
    try {
      const response = await fetch(`/api/pipeline/${id}/result`);
      if (!response.ok) throw new Error("The final transcript could not be loaded. Please contact your administrator.");
      setTranscript((await response.json()) as FinalTranscript);
      setBackendError(null);
    } catch (error) {
      setBackendError(error instanceof Error ? error.message : "The final transcript could not be loaded.");
    }
  }, []);

  const listenToRun = useCallback((id: string, url: string) => {
    eventSource.current?.close();
    const source = new EventSource(url);
    eventSource.current = source;
    source.onmessage = (message) => {
      const event = JSON.parse(message.data) as ProgressEvent;
      const clientMessage = clientProgressMessage(event);
      setCurrentStage(event.stage);
      setCurrentOperation(clientMessage);
      setPercent(event.percent);
      setStages(event.stages);
      setEvents((current) => [...current.slice(-11), { ...event, message: clientMessage }]);
      setStreamReconnecting(false);
      if (event.run_status === "failed") {
        setRunStatus("failed");
        setBackendError(clientMessage);
        source.close();
      } else if (event.run_status === "completed") {
        setRunStatus("completed");
        source.close();
        void loadFinalResult(id);
      } else {
        setRunStatus("running");
      }
    };
    source.onerror = () => setStreamReconnecting(true);
  }, [loadFinalResult]);

  const startProcessing = async () => {
    if (!selectedFile || processing) return;
    setUploadError(null);
    setBackendError(null);
    setTranscript(null);
    setEvents([]);
    setStages(INITIAL_STAGES);
    setPercent(0);
    setRunStatus("queued");
    setStartedAt(Date.now());
    setElapsedSeconds(0);
    setCurrentOperation("Sending the recording for processing.");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("speech_provider", speechProvider);
      const response = await fetch("/api/pipeline/start", { method: "POST", body: formData });
      if (!response.ok) {
        throw new Error("The recording could not be submitted. Please contact your administrator.");
      }
      const run = (await response.json()) as StartResponse;
      setSpeechProvider(run.speech_provider);
      setRunId(run.run_id);
      listenToRun(run.run_id, run.events_url);
    } catch (error) {
      setRunStatus("failed");
      setStartedAt(null);
      setBackendError(error instanceof Error ? error.message : "The recording could not be submitted.");
    }
  };

  const startAnother = () => {
    eventSource.current?.close();
    setRunId(null);
    setRunStatus("idle");
    setSelectedFile(null);
    setAudioDuration(null);
    setCurrentStage(null);
    setStages(INITIAL_STAGES);
    setEvents([]);
    setPercent(0);
    setCurrentOperation("Select a recording to begin.");
    setTranscript(null);
    setStartedAt(null);
    setElapsedSeconds(0);
    setBackendError(null);
    setStreamReconnecting(false);
  };

  const transcriptSummary = useMemo(() => {
    if (!transcript) return null;
    const utterances = transcript.utterances ?? [];
    const participantIds = new Set(
      utterances.map((utterance) => utterance.canonical_speaker_id).filter(Boolean),
    );
    const timedEnds = utterances
      .map((utterance) => utterance.end_seconds)
      .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
    const speakerCount = transcript.speaker_registry?.length || participantIds.size;
    const needsReview =
      transcript.processing_status === "NEEDS_REVIEW" ||
      Boolean(transcript.review_flags?.length) ||
      Boolean(transcript.speaker_registry?.some((speaker) => speaker.review_required)) ||
      utterances.some((utterance) => utterance.attribution_status === "NEEDS_REVIEW");
    return {
      utterances,
      participantCount: speakerCount,
      duration: timedEnds.length ? Math.max(...timedEnds) : null,
      needsReview,
    };
  }, [transcript]);

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null || !Number.isFinite(seconds)) return "—";
    const whole = Math.max(0, Math.floor(seconds));
    const hours = Math.floor(whole / 3600);
    const minutes = Math.floor((whole % 3600) / 60);
    const remainder = whole % 60;
    return hours > 0
      ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
      : `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
  };

  const stageIcon = (key: StageKey) => {
    if (stages[key].status === "completed") return <Icon name="check" />;
    if (stages[key].status === "failed") return <Icon name="alert" />;
    if (stages[key].status === "in_progress") return <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-aqua" />;
    return <Icon name={key === "audio_upload" ? "upload" : key === "speech_transcription" ? "wave" : key === "llm_reconstruction" ? "users" : "file"} />;
  };

  const statusLabel =
    runStatus === "failed" ? "Needs attention"
      : runStatus === "completed" ? "Transcript ready"
        : processing ? "In progress" : "Ready when you are";
  const statusTone =
    runStatus === "failed" ? "border-rose-400/40 bg-rose-400/10 text-rose-200"
      : runStatus === "completed" ? "border-mint/40 bg-mint/10 text-emerald-200"
        : processing ? "border-aqua/40 bg-aqua/10 text-cyan-100" : "border-white/10 bg-white/5 text-slate-300";
  const journeyDone = runStatus === "completed" ? 2 : processing ? 1 : 0;

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-night font-sans text-slate-100">
      <Backdrop />

      <header className="sticky top-0 z-40 border-b border-white/[0.07] bg-night/60 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between gap-4 px-4 py-3.5 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-aqua via-iris to-rose2 shadow-glow">
              <Icon name="wave" className="h-5 w-5 text-white" />
            </div>
            <div className="leading-tight">
              <div className="font-display text-[15px] font-semibold tracking-tight text-white">Ambient Clinical</div>
              <div className="text-[10px] font-medium uppercase tracking-[0.22em] text-slate-400">Listening platform</div>
            </div>
          </div>
          <ConnectionPill
            good={backendOnline && voiceStatus.good}
            label={backendOnline ? voiceStatus.label : "Workspace unavailable"}
          />
        </div>
      </header>

      <main className="relative mx-auto max-w-[1280px] px-4 pb-16 pt-10 sm:px-8 lg:pt-16">
        {/* ───────── Hero ───────── */}
        <section className="grid grid-cols-1 items-center gap-10 lg:grid-cols-[1.02fr_0.98fr] lg:gap-14">
          <motion.div className="min-w-0" variants={stagger} initial="hidden" animate="show">
            <motion.div variants={rise} className="chip border-aqua/30 bg-aqua/10 text-cyan-100">
              <Sparkles className="h-3.5 w-3.5" /> Hands-free · Always listening
            </motion.div>
            <motion.h1
              variants={rise}
              className="mt-5 font-display text-[40px] font-semibold leading-[1.04] tracking-[-0.04em] text-white sm:text-[58px]"
            >
              Every consultation,<br />
              <span className="gradient-text">turned into a clinical note.</span>
            </motion.h1>
            <motion.p variants={rise} className="mt-6 max-w-[560px] text-base leading-7 text-slate-400">
              Just talk. Ambient Clinical captures the conversation, writes the transcript, picks out the
              clinical details, and prepares the SOAP note — so you can stay with your patient.
            </motion.p>
            <motion.div variants={rise}>
              <Journey done={journeyDone} active={processing} />
            </motion.div>
          </motion.div>

          <motion.section
            initial={{ opacity: 0, y: 30, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15, ease: [0.2, 0.8, 0.2, 1] }}
            className="relative min-w-0"
          >
            <div className="absolute -inset-px rounded-[28px] bg-gradient-to-br from-aqua/50 via-iris/30 to-rose2/40 opacity-60 blur-md" aria-hidden="true" />
            <div className="glass relative !rounded-[28px] bg-panel/80 p-5 sm:p-7">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <p className="kicker">New encounter</p>
                  <h2 className="mt-1.5 font-display text-[22px] font-semibold tracking-tight text-white">Start with a recording</h2>
                  <p className="mt-1.5 text-[13px] leading-5 text-slate-400">
                    Upload a conversation to create the transcript and move it toward the final note.
                  </p>
                </div>
                <Equalizer active={processing} />
              </div>

              <input
                ref={fileInput}
                type="file"
                accept=".wav,audio/wav"
                className="hidden"
                onChange={handleFileInput}
                aria-label="Select recording"
              />
              <div
                onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => !processing && !selectedFile && fileInput.current?.click()}
                className={`group relative flex cursor-pointer flex-col gap-4 overflow-hidden rounded-2xl border border-dashed p-5 transition-all duration-300 sm:flex-row sm:items-center sm:justify-between ${
                  dragging
                    ? "border-aqua bg-aqua/10 shadow-glow"
                    : selectedFile
                      ? "border-mint/40 bg-mint/[0.06]"
                      : "border-white/15 bg-white/[0.03] hover:border-aqua/50 hover:bg-white/[0.06]"
                }`}
              >
                <div className="flex min-w-0 items-center gap-4">
                  <motion.div
                    animate={dragging ? { scale: 1.15, y: -3 } : { scale: 1, y: 0 }}
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-aqua/25 to-iris/25 text-cyan-200 ring-1 ring-white/10"
                  >
                    <Icon name={selectedFile ? "file" : "upload"} className="h-5 w-5" />
                  </motion.div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-white">
                      {selectedFile ? selectedFile.name : "Drop your recording here"}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {selectedFile
                        ? `${formatBytes(selectedFile.size)} · ${formatDuration(audioDuration)}`
                        : "WAV audio · or browse from your device"}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2" onClick={(event) => event.stopPropagation()}>
                  {selectedFile && !processing && (
                    <button
                      type="button"
                      onClick={() => { setSelectedFile(null); setUploadError(null); }}
                      className="btn-ghost"
                      aria-label="Remove selected recording"
                    >
                      Remove
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => fileInput.current?.click()}
                    disabled={processing}
                    className="btn-ghost"
                  >
                    {selectedFile ? "Change file" : "Browse files"}
                  </button>
                </div>
              </div>

              {uploadError && (
                <p role="alert" className="mt-3 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-xs text-rose-200">{uploadError}</p>
              )}

              <fieldset className="mt-5 min-w-0 border-0 p-0" disabled={processing}>
                <legend className="mb-2.5 p-0 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Transcription style
                </legend>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {SPEECH_PROVIDER_OPTIONS.map((option) => {
                    const configured = Boolean(speechProviders[option.id]?.configured);
                    const selected = speechProvider === option.id;
                    return (
                      <label
                        key={option.id}
                        className={`relative flex cursor-pointer gap-3 rounded-2xl border p-4 transition-all duration-300 ${
                          selected
                            ? "border-aqua/60 bg-aqua/[0.09] shadow-[0_0_32px_-10px_rgba(34,211,238,0.6)]"
                            : "border-white/10 bg-white/[0.03] hover:border-white/25"
                        } ${!configured ? "cursor-not-allowed opacity-45" : ""}`}
                      >
                        <input
                          type="radio"
                          name="speech-provider"
                          value={option.id}
                          checked={selected}
                          disabled={!configured}
                          onChange={() => setSpeechProvider(option.id)}
                          className="sr-only"
                        />
                        <span
                          aria-hidden="true"
                          className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition ${
                            selected ? "border-aqua" : "border-slate-500"
                          }`}
                        >
                          <span className={`h-2 w-2 rounded-full bg-aqua transition ${selected ? "scale-100" : "scale-0"}`} />
                        </span>
                        <span className="min-w-0">
                          <span className="block text-[13px] font-semibold text-white">{option.title}</span>
                          <span className="mt-0.5 block text-[11px] leading-4 text-slate-400">
                            {configured ? option.description : "Currently unavailable"}
                          </span>
                        </span>
                      </label>
                    );
                  })}
                </div>
                {speechProvider === "foundry_fast" && (
                  <p className="mt-3 text-[11px] leading-5 text-slate-500">Recordings up to 250 MB are supported with this style.</p>
                )}
              </fieldset>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
                <div className="flex min-w-0 items-center gap-2 text-[11px] text-slate-500">
                  <Icon name="shield" className="h-4 w-4 shrink-0 text-mint" />
                  <span>Private and secure</span>
                </div>
                {runStatus === "completed" || runStatus === "failed" ? (
                  <button type="button" onClick={startAnother} className="btn-primary">
                    <Icon name="refresh" /> New recording
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={startProcessing}
                    disabled={!selectedFile || processing || !backendOnline || !azureConfigured || !selectedProviderConfigured}
                    className="btn-primary"
                  >
                    {processing
                      ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-night/30 border-t-night" />
                      : <Icon name="play" />}
                    {processing ? "Working on it…" : "Create transcript"}
                    {!processing && <Icon name="arrow" className="h-4 w-4" />}
                  </button>
                )}
              </div>

              {backendOnline && (!azureConfigured || !selectedProviderConfigured) && (
                <p role="status" className="mt-3 rounded-xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-xs leading-5 text-amber-100">
                  Transcription is not available for this workspace right now. Please contact your administrator.
                </p>
              )}
              {!backendOnline && (
                <p role="status" className="mt-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-xs leading-5 text-slate-300">
                  The workspace is offline. Start the service, then refresh this page.
                </p>
              )}
            </div>
          </motion.section>
        </section>

        {/* ───────── Hands-free voice ───────── */}
        <Reveal className="mt-14">
          <section className="glass overflow-hidden p-6 sm:p-9">
            <div className="grid grid-cols-1 items-center gap-8 md:grid-cols-[auto_minmax(0,1fr)]">
              <AshaOrb />
              <div>
                <p className="kicker">Meet Asha</p>
                <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-white sm:text-[30px]">
                  Your hands-free clinical assistant
                </h2>
                <p className="mt-2 max-w-[620px] text-sm leading-6 text-slate-400">
                  No clicks, no typing. Asha only listens when you call her, and records only when you ask.
                </p>
                <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <VoiceCue step="1" phrase="“Hey Asha”" hint="Wakes Asha up" tone="from-aqua/25" />
                  <VoiceCue step="2" phrase="“Start recording”" hint="Begins the consultation" tone="from-mint/25" />
                  <VoiceCue step="3" phrase="“Hey Asha, stop recording”" hint="Saves it instantly" tone="from-rose2/25" />
                </div>
              </div>
            </div>
          </section>
        </Reveal>

        {/* ───────── Workflow ───────── */}
        <Reveal className="mt-6">
          <section className="glass p-6 sm:p-8">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="kicker">Your workflow</p>
                <h2 className="mt-1.5 font-display text-xl font-semibold tracking-tight text-white">Progress of this encounter</h2>
              </div>
              <span className={`rounded-full border px-3.5 py-1.5 text-[11px] font-semibold ${statusTone}`}>{statusLabel}</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {STAGE_ORDER.map((key, index) => {
                const stage = stages[key];
                const state = stage.status;
                return (
                  <motion.div
                    key={key}
                    layout
                    className={`relative overflow-hidden rounded-2xl border p-4 transition-colors duration-500 ${
                      state === "in_progress" ? "border-aqua/50 bg-aqua/[0.08]"
                        : state === "completed" ? "border-mint/40 bg-mint/[0.07]"
                          : state === "failed" ? "border-rose-400/40 bg-rose-400/[0.08]"
                            : "border-white/10 bg-white/[0.03]"
                    }`}
                  >
                    {state === "in_progress" && (
                      <span className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-aqua to-transparent" aria-hidden="true" />
                    )}
                    <div className="flex items-center justify-between">
                      <span className="font-display text-xs font-semibold tracking-widest text-slate-500">{String(index + 1).padStart(2, "0")}</span>
                      <span className={`flex h-8 w-8 items-center justify-center rounded-xl ${
                        state === "completed" ? "bg-mint/20 text-emerald-200"
                          : state === "failed" ? "bg-rose-400/20 text-rose-200"
                            : state === "in_progress" ? "bg-aqua/20 text-cyan-100" : "bg-white/5 text-slate-400"
                      }`}>{stageIcon(key)}</span>
                    </div>
                    <div className="mt-4 text-[13px] font-semibold text-white">{stage.label}</div>
                    <div className="mt-1 text-[11px] text-slate-400">
                      {state === "waiting" ? "Up next" : state === "in_progress" ? "In progress" : state === "completed" ? "Complete" : "Needs attention"}
                    </div>
                  </motion.div>
                );
              })}
            </div>
            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between gap-4 text-xs">
                <span className="truncate font-medium text-slate-300">{currentOperation}</span>
                <span className="shrink-0 font-display font-semibold tabular-nums text-white">{percent}%</span>
              </div>
              <div className="relative h-2.5 overflow-hidden rounded-full bg-white/[0.07]">
                <motion.div
                  className="relative h-full overflow-hidden rounded-full bg-gradient-to-r from-aqua via-mint to-iris"
                  initial={false}
                  animate={{ width: `${percent}%` }}
                  transition={{ type: "spring", stiffness: 70, damping: 18 }}
                >
                  {processing && <span className="absolute inset-0 animate-shimmer bg-gradient-to-r from-transparent via-white/50 to-transparent" />}
                </motion.div>
              </div>
            </div>
          </section>
        </Reveal>

        {/* ───────── Activity ───────── */}
        <Reveal className="mt-6">
          <section className="glass overflow-hidden">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.07] px-6 py-5 sm:px-8">
              <div className="flex items-center gap-3">
                <span className={`relative flex h-10 w-10 items-center justify-center rounded-2xl ${processing ? "bg-aqua/20 text-cyan-100" : "bg-white/5 text-slate-300"}`}>
                  {processing && <span className="absolute inset-0 animate-ring rounded-2xl border border-aqua/60" />}
                  <Icon name="activity" className="h-5 w-5" />
                </span>
                <div>
                  <h2 className="font-display text-base font-semibold tracking-tight text-white">Live activity</h2>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {processing ? "Updates appear here as each step completes." : "Progress will appear here once you begin."}
                  </p>
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-2 text-right">
                <div className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-500">Elapsed</div>
                <div className="font-display text-[17px] font-semibold tabular-nums text-white">{formatDuration(elapsedSeconds)}</div>
              </div>
            </div>
            <div className="px-6 py-5 sm:px-8">
              {streamReconnecting && processing && (
                <div className="mb-3 rounded-xl bg-amber-300/10 px-3 py-2 text-[11px] text-amber-100">
                  Reconnecting to live updates. Your recording keeps processing.
                </div>
              )}
              {processing && elapsedSeconds >= 120 && (
                <div role="status" className="mb-3 rounded-xl bg-aqua/10 px-3 py-2 text-[11px] leading-5 text-cyan-100">
                  This recording is taking a little longer than usual. Please keep this page open.
                </div>
              )}
              {backendError && (
                <div role="alert" className="mb-3 rounded-2xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-xs leading-5 text-rose-100">
                  <div className="mb-1 font-bold">We couldn’t finish this recording</div>
                  {backendError}
                </div>
              )}
              <div className="scrollbar-subtle max-h-[300px] min-h-[140px] space-y-3 overflow-y-auto pr-2">
                {events.length === 0 ? (
                  <div className="flex min-h-[140px] flex-col items-center justify-center text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/5 text-slate-400">
                      <Icon name="activity" className="h-5 w-5" />
                    </div>
                    <p className="mt-3 text-xs font-semibold text-slate-300">Ready for your recording</p>
                    <p className="mt-1 max-w-[300px] text-[11px] leading-5 text-slate-500">Each completed step shows up here in real time.</p>
                  </div>
                ) : (
                  <AnimatePresence initial={false}>
                    {events.map((event) => (
                      <motion.div
                        key={event.sequence}
                        initial={{ opacity: 0, x: -14 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex gap-3"
                      >
                        <span className={`mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                          event.status === "failed" ? "bg-rose-400/20 text-rose-200"
                            : event.status === "completed" ? "bg-mint/20 text-emerald-200" : "bg-aqua/15 text-cyan-200"
                        }`}>
                          {event.status === "completed" ? <Icon name="check" className="h-3 w-3" />
                            : event.status === "failed" ? <Icon name="alert" className="h-3 w-3" />
                              : <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="text-[13px] leading-5 text-slate-200">{event.message}</div>
                          <div className="mt-0.5 text-[10px] text-slate-500">
                            {event.stage ? event.stages[event.stage]?.label : "Workflow"} <span className="px-1">·</span> {formatClock(event.timestamp)}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                )}
              </div>
            </div>
          </section>
        </Reveal>

        {/* ───────── Transcript ───────── */}
        <AnimatePresence>
          {transcript && transcriptSummary && (
            <motion.section
              ref={transcriptPanel}
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
              className="glass mt-6 overflow-hidden"
            >
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/[0.07] px-6 py-6 sm:px-8">
                <div>
                  <p className="kicker">Step 2 complete</p>
                  <h2 className="mt-1.5 font-display text-2xl font-semibold tracking-tight text-white">Conversation transcript</h2>
                  <p className="mt-1.5 text-xs text-slate-400">
                    {transcript.encounter_id ? `Encounter ${transcript.encounter_id}` : "Reconstructed conversation"} · Draft for clinician review
                  </p>
                </div>
                <span className={`rounded-full border px-3.5 py-1.5 text-[11px] font-semibold ${
                  transcriptSummary.needsReview
                    ? "border-amber-300/40 bg-amber-300/10 text-amber-100"
                    : "border-aqua/40 bg-aqua/10 text-cyan-100"
                }`}>
                  {transcriptSummary.needsReview ? "Review suggested" : "Draft"}
                </span>
              </div>

              {transcriptSummary.needsReview && (
                <div className="mx-6 mt-5 flex gap-3 rounded-2xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 sm:mx-8">
                  <Icon name="alert" className="mt-0.5 shrink-0 text-amber-200" />
                  <div className="text-[12px] leading-5 text-amber-100">
                    Some parts of this transcript need a clinician’s review before they are relied on.
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 px-6 py-6 sm:grid-cols-4 sm:px-8">
                <SummaryMetric label="Utterances" value={transcriptSummary.utterances.length} />
                <SummaryMetric label="Participants" value={transcriptSummary.participantCount} />
                <SummaryMetric label="Duration" text={formatDuration(transcriptSummary.duration)} />
                <SummaryMetric label="Status" text={humanStatus(transcript.processing_status)} />
              </div>

              <div className="scrollbar-subtle mx-4 mb-6 max-h-[620px] space-y-4 overflow-y-auto rounded-2xl bg-black/20 p-4 sm:mx-8 sm:p-6">
                {transcriptSummary.utterances.map((utterance, index) => (
                  <TranscriptRow
                    key={utterance.utterance_id || `${utterance.start_seconds ?? "time"}-${index}`}
                    index={index}
                    utterance={utterance}
                    speakers={transcript.speaker_registry ?? []}
                    formatDuration={formatDuration}
                  />
                ))}
                {transcriptSummary.utterances.length === 0 && (
                  <div className="py-8 text-center text-xs text-slate-400">No conversation was found in this recording.</div>
                )}
              </div>

              <div className="grid grid-cols-1 gap-3 border-t border-white/[0.07] px-6 py-6 sm:grid-cols-2 sm:px-8">
                <NextStep icon="pulse" title="Clinical entities" text="Symptoms, medications, findings and follow-ups are picked out of the conversation." />
                <NextStep icon="note" title="SOAP note" text="The structured note is drafted from the transcript, ready for your review." />
              </div>
            </motion.section>
          )}
        </AnimatePresence>

        <footer className="mt-12 flex flex-col gap-2 border-t border-white/[0.07] px-1 pt-6 text-[11px] leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <span>Ambient Clinical <span className="px-1">·</span> From conversation to SOAP note</span>
          <span>Drafts are for clinician review and are not a substitute for clinical judgment.</span>
        </footer>
      </main>

      <VoiceAssistant backendOnline={backendOnline} onStatusChange={setVoiceStatus} />
    </div>
  );
}

/* ───────────────────────── Presentational pieces ───────────────────────── */

const rise: Variants = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.2, 0.8, 0.2, 1] } },
};
const stagger: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.1 } } };

function Reveal({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 36 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
}

function Backdrop() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
      <div className="absolute -left-[12%] -top-[18%] h-[60vmax] w-[60vmax] animate-drift rounded-full bg-aqua/20 blur-[120px]" />
      <div className="absolute -right-[16%] top-[8%] h-[52vmax] w-[52vmax] animate-drift-slow rounded-full bg-iris/25 blur-[130px]" />
      <div className="absolute -bottom-[26%] left-[22%] h-[50vmax] w-[50vmax] animate-drift rounded-full bg-rose2/[0.14] blur-[130px]" />
      <div className="bg-grid absolute inset-0" />
    </div>
  );
}

function Journey({ done, active }: { done: number; active: boolean }) {
  const steps = [
    { icon: "mic" as const, label: "Conversation", sub: "Captured" },
    { icon: "file" as const, label: "Transcript", sub: "Speaker by speaker" },
    { icon: "pulse" as const, label: "Clinical entities", sub: "Extracted" },
    { icon: "note" as const, label: "SOAP note", sub: "Ready to review" },
  ];
  return (
    <div className="mt-9 grid grid-cols-2 gap-3 sm:grid-cols-4">
      {steps.map((step, index) => {
        const complete = index < done;
        const lit = complete || (index === done && active);
        return (
          <motion.div
            key={step.label}
            whileHover={{ y: -4 }}
            className={`relative overflow-hidden rounded-2xl border p-3.5 transition-colors duration-500 ${
              complete ? "border-mint/40 bg-mint/[0.08]" : lit ? "border-aqua/50 bg-aqua/[0.09]" : "border-white/10 bg-white/[0.03]"
            }`}
          >
            <div className="mb-3 flex items-center justify-between">
              <span className={`flex h-8 w-8 items-center justify-center rounded-xl ${complete ? "bg-mint/20 text-emerald-200" : lit ? "bg-aqua/20 text-cyan-100" : "bg-white/5 text-slate-400"}`}>
                <Icon name={complete ? "check" : step.icon} className="h-4 w-4" />
              </span>
              <span className="font-display text-[10px] font-semibold tracking-widest text-slate-600">0{index + 1}</span>
            </div>
            <div className="text-[13px] font-semibold text-white">{step.label}</div>
            <div className="mt-0.5 text-[11px] text-slate-400">{step.sub}</div>
            {lit && !complete && <span className="absolute inset-x-0 bottom-0 h-0.5 animate-shimmer bg-gradient-to-r from-transparent via-aqua to-transparent" />}
          </motion.div>
        );
      })}
    </div>
  );
}

function Equalizer({ active }: { active: boolean }) {
  return (
    <div className="flex h-9 shrink-0 items-end gap-[3px]" aria-hidden="true">
      {[0.2, 0.55, 0.9, 0.4, 0.75, 0.3, 0.6].map((delay, index) => (
        <span
          key={index}
          className={`h-full w-[3px] origin-bottom rounded-full bg-gradient-to-t from-aqua to-iris ${active ? "animate-bar" : "opacity-40"}`}
          style={{ animationDelay: `${delay}s`, transform: active ? undefined : `scaleY(${0.25 + (index % 3) * 0.2})` }}
        />
      ))}
    </div>
  );
}

function AshaOrb() {
  return (
    <div className="relative mx-auto flex h-40 w-40 items-center justify-center sm:h-48 sm:w-48" aria-hidden="true">
      <span className="absolute inset-0 animate-ring rounded-full border border-aqua/40" />
      <span className="absolute inset-0 animate-ring rounded-full border border-iris/40 [animation-delay:1.2s]" />
      <span className="absolute inset-3 animate-spin-slow rounded-full bg-[conic-gradient(from_0deg,#22d3ee,#8b5cf6,#f472b6,#34d399,#22d3ee)] opacity-90 blur-[10px]" />
      <span className="absolute inset-[14px] animate-spin-slow rounded-full bg-[conic-gradient(from_180deg,#22d3ee,#8b5cf6,#f472b6,#34d399,#22d3ee)] [animation-direction:reverse]" />
      <span className="absolute inset-[26px] rounded-full bg-night/90 shadow-[inset_0_0_30px_rgba(139,92,246,0.5)]" />
      <div className="relative"><Equalizer active /></div>
    </div>
  );
}

function VoiceCue({ step, phrase, hint, tone }: { step: string; phrase: string; hint: string; tone: string }) {
  return (
    <motion.div
      whileHover={{ y: -5, scale: 1.02 }}
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${tone} to-transparent p-4`}
    >
      <span className="font-display text-[11px] font-semibold tracking-widest text-slate-400">STEP {step}</span>
      <div className="mt-2 font-display text-[15px] font-semibold leading-snug text-white">{phrase}</div>
      <div className="mt-1 text-[11px] text-slate-400">{hint}</div>
    </motion.div>
  );
}

function NextStep({ icon, title, text }: { icon: "pulse" | "note"; title: string; text: string }) {
  return (
    <div className="relative flex gap-4 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-iris/10 to-transparent p-4">
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/5 text-violet-200 ring-1 ring-white/10">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <div>
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          {title}
          <span className="rounded-full bg-iris/20 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest text-violet-200">Up next</span>
        </div>
        <p className="mt-1 text-xs leading-5 text-slate-400">{text}</p>
      </div>
      <span className="absolute inset-x-0 bottom-0 h-px animate-shimmer bg-gradient-to-r from-transparent via-violet-300/70 to-transparent" />
    </div>
  );
}

function TranscriptRow({
  utterance,
  speakers,
  formatDuration,
  index,
}: {
  utterance: TranscriptUtterance;
  speakers: Speaker[];
  formatDuration: (seconds: number | null) => string;
  index: number;
}) {
  const speaker = speakers.find((item) => item.canonical_speaker_id === utterance.canonical_speaker_id);
  const role = (utterance.role || speaker?.role || "UNKNOWN").toUpperCase();
  const label = speaker?.display_name || speaker?.name || utterance.canonical_speaker_id || "Unidentified participant";
  const start = formatTime(utterance.start_seconds);
  const duration =
    typeof utterance.duration_seconds === "number"
      ? utterance.duration_seconds
      : typeof utterance.start_seconds === "number" && typeof utterance.end_seconds === "number"
        ? utterance.end_seconds - utterance.start_seconds
        : null;
  const clinician = role === "DOCTOR" || role === "NURSE" || role === "PHARMACIST";

  return (
    <motion.article
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "40px" }}
      transition={{ duration: 0.45, delay: Math.min(index, 6) * 0.04 }}
      className={`flex ${clinician ? "justify-start" : "justify-end"}`}
    >
      <div className={`max-w-[92%] sm:max-w-[78%] ${clinician ? "" : "text-right"}`}>
        <div className={`mb-1.5 flex flex-wrap items-center gap-2 ${clinician ? "" : "justify-end"}`}>
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-wider ring-1 ring-inset ${ROLE_STYLES[role] || ROLE_STYLES.UNKNOWN}`}>
            {role.replace(/_/g, " ")}
          </span>
          <span className="max-w-[180px] truncate text-[10px] text-slate-500" title={label}>{label}</span>
          <span className="text-[10px] tabular-nums text-slate-600">{start} · {formatDuration(duration)}</span>
        </div>
        <p className={`m-0 whitespace-pre-wrap break-words rounded-2xl px-4 py-3 text-left text-[13px] leading-6 text-slate-100 ${
          clinician
            ? "rounded-tl-md border border-aqua/20 bg-gradient-to-br from-aqua/[0.12] to-aqua/[0.03]"
            : "rounded-tr-md border border-iris/25 bg-gradient-to-br from-iris/[0.14] to-iris/[0.04]"
        }`}>
          {utterance.text || "No transcript text available."}
        </p>
      </div>
    </motion.article>
  );
}

function CountUp({ value }: { value: number }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const controls = animate(0, value, { duration: 1.1, ease: "easeOut", onUpdate: (latest) => setShown(Math.round(latest)) });
    return () => controls.stop();
  }, [value]);
  return <>{shown}</>;
}

function SummaryMetric({ label, value, text }: { label: string; value?: number; text?: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3.5">
      <div className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="mt-1.5 truncate font-display text-xl font-semibold text-white" title={text}>
        {typeof value === "number" ? <CountUp value={value} /> : text}
      </div>
    </div>
  );
}

function ConnectionPill({ good, label }: { good: boolean; label: string }) {
  return (
    <div className="flex max-w-[60vw] items-center gap-2.5 rounded-full border border-white/10 bg-white/5 px-3.5 py-2 backdrop-blur">
      <span className="relative flex h-2.5 w-2.5 shrink-0">
        {good && <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-70" />}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${good ? "bg-mint" : "bg-amber-400"}`} />
      </span>
      <span className="truncate text-[11px] font-semibold text-slate-200">{label}</span>
    </div>
  );
}

function humanStatus(status?: string): string {
  if (!status) return "Available";
  const text = status.replace(/_/g, " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const ICONS = {
  check: Check,
  alert: TriangleAlert,
  upload: UploadCloud,
  wave: AudioLines,
  users: Users,
  file: FileText,
  mic: Mic,
  play: Play,
  refresh: RotateCcw,
  activity: Activity,
  shield: ShieldCheck,
  info: Info,
  arrow: ArrowRight,
  pulse: Stethoscope,
  note: ClipboardList,
};

function Icon({ name, className = "" }: { name: keyof typeof ICONS; className?: string }) {
  const Glyph = ICONS[name];
  return <Glyph className={`h-4 w-4 ${className}`} strokeWidth={1.8} aria-hidden="true" />;
}

function formatTime(seconds: number | null | undefined): string {
  if (typeof seconds !== "number" || !Number.isFinite(seconds)) return "—";
  const whole = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const remainder = whole % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function formatClock(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default App;
