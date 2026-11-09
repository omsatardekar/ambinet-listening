import { ChangeEvent, DragEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  DOCTOR: "bg-blue-50 text-blue-800 ring-blue-100",
  PATIENT: "bg-teal-50 text-teal-800 ring-teal-100",
  NURSE: "bg-violet-50 text-violet-800 ring-violet-100",
  CAREGIVER: "bg-amber-50 text-amber-800 ring-amber-100",
  FAMILY_MEMBER: "bg-orange-50 text-orange-800 ring-orange-100",
  PHARMACIST: "bg-cyan-50 text-cyan-800 ring-cyan-100",
  UNKNOWN: "bg-slate-100 text-slate-700 ring-slate-200",
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
  const [currentOperation, setCurrentOperation] = useState("Select a WAV recording to begin.");
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
      setUploadError("Only WAV recordings are supported by this pipeline.");
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
    setCurrentOperation("Select a WAV recording to begin.");
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
    if (stages[key].status === "in_progress") return <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-teal" />;
    return <Icon name={key === "audio_upload" ? "upload" : key === "speech_transcription" ? "wave" : key === "llm_reconstruction" ? "users" : "file"} />;
  };

  return (
    <div className="app-shell min-h-screen text-ink">
      <header className="app-header">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-5 px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="brand-mark"><Icon name="wave" className="h-5 w-5" /></div>
            <div>
              <div className="text-[15px] font-bold tracking-[-0.03em] text-[#17314b]">Ambient Clinical</div>
              <div className="mt-0.5 text-[11px] font-medium tracking-wide text-muted">LISTENING PLATFORM</div>
            </div>
          </div>
          <ConnectionPill
            good={backendOnline && voiceStatus.good}
            label={backendOnline ? voiceStatus.label : "Workspace unavailable"}
          />
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-5 pb-12 pt-8 sm:px-8 lg:pt-12">
        <section className="mb-8 grid items-center gap-8 lg:grid-cols-[0.82fr_1.18fr] lg:gap-12">
          <div className="py-2">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#d6e8e4] bg-white/80 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-[#287a72]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#39a995]" />
              Ambient clinical listening platform
            </div>
            <h1 className="max-w-[620px] text-[38px] font-semibold leading-[1.08] tracking-[-0.055em] text-[#17314b] sm:text-[50px]">
              One platform for <span className="text-[#267c74]">connected clinical workflows.</span>
            </h1>
            <p className="mt-5 max-w-[530px] text-[15px] leading-7 text-[#65788a]">
              From encounter audio and speaker-aware transcripts to structured clinical context, documentation, and clinician review.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-3 text-xs font-medium text-[#526b7a]">
              <span className="inline-flex items-center gap-2"><Icon name="wave" className="h-4 w-4 text-[#38877e]" /> Conversation intelligence</span>
              <span className="inline-flex items-center gap-2"><Icon name="users" className="h-4 w-4 text-[#38877e]" /> Clinician-led review</span>
            </div>
          </div>

          <section className="upload-card">
            <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="section-kicker">RECORDING & TRANSCRIPTION</p>
                <h2 className="mt-1.5 text-[20px] font-semibold tracking-[-0.03em] text-[#17314b]">Start an encounter</h2>
                <p className="mt-1.5 text-xs leading-5 text-muted">Upload a WAV recording to create the encounter transcript.</p>
              </div>
              <span className="file-format-badge">WAV AUDIO</span>
            </div>

            <input
              ref={fileInput}
              type="file"
              accept=".wav,audio/wav"
              className="hidden"
              onChange={handleFileInput}
              aria-label="Select WAV recording"
            />
            <div
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`upload-dropzone ${dragging ? "drop-active" : ""}`}
            >
              <div className="flex min-w-0 items-center gap-4">
                <div className="upload-icon"><Icon name="upload" className="h-5 w-5" /></div>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-[#17314b]">
                    {selectedFile ? selectedFile.name : "Drop your audio recording here"}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    {selectedFile
                      ? `${formatBytes(selectedFile.size)} · ${formatDuration(audioDuration)}`
                      : "WAV format · or choose a file from your device"}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3 sm:mt-0">
                {selectedFile && !processing && (
                  <button
                    type="button"
                    onClick={() => { setSelectedFile(null); setUploadError(null); }}
                    className="quiet-button"
                    aria-label="Remove selected recording"
                  >
                    Remove
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => fileInput.current?.click()}
                  disabled={processing}
                  className="secondary-button"
                >
                  {selectedFile ? "Change file" : "Browse files"}
                </button>
              </div>
            </div>

            {uploadError && <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-4 py-3 text-xs text-rose-700">{uploadError}</p>}

            <fieldset className="provider-fieldset mt-5" disabled={processing}>
              <legend className="provider-legend">Choose transcription approach</legend>
              <div className="provider-options">
                {SPEECH_PROVIDER_OPTIONS.map((option) => {
                  const configured = Boolean(speechProviders[option.id]?.configured);
                  return (
                    <label
                      key={option.id}
                      className={`provider-option ${
                        speechProvider === option.id ? "provider-option-selected" : ""
                      } ${!configured ? "provider-option-unavailable" : ""}`}
                    >
                      <input
                        type="radio"
                        name="speech-provider"
                        value={option.id}
                        checked={speechProvider === option.id}
                        disabled={!configured}
                        onChange={() => setSpeechProvider(option.id)}
                      />
                      <span className="provider-radio" aria-hidden="true" />
                      <span className="provider-copy">
                        <span className="provider-heading">
                          <span className="provider-title">{option.title}</span>
                          <span className="provider-badge">
                            {configured ? option.subtitle : "Configuration needed"}
                          </span>
                        </span>
                        <span className="provider-description">{option.description}</span>
                        {!configured && (
                          <span className="provider-setup">
                            This approach is currently unavailable.
                          </span>
                        )}
                      </span>
                    </label>
                  );
                })}
              </div>
              {speechProvider === "foundry_fast" && (
                <p className="provider-footnote">
                  Fast transcription accepts WAV files smaller than 250 MB. Transcription,
                  speaker structuring, and final review output continue through the shared workflow.
                </p>
              )}
            </fieldset>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex min-w-0 items-center gap-2 text-[11px] text-[#738495]">
                <Icon name="shield" className="h-4 w-4 shrink-0 text-[#39877d]" />
                <span>Recording handled by your configured clinical workflow.</span>
              </div>
              {runStatus === "completed" || runStatus === "failed" ? (
                <button type="button" onClick={startAnother} className="primary-button">
                  <Icon name="refresh" />
                  New recording
                </button>
              ) : (
                <button
                  type="button"
                  onClick={startProcessing}
                  disabled={!selectedFile || processing || !backendOnline || !azureConfigured || !selectedProviderConfigured}
                  className="primary-button disabled:cursor-not-allowed disabled:opacity-45"
                >
                  {processing
                    ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                    : <Icon name="play" />}
                  {processing ? "Processing…" : "Create transcript"}
                  {!processing && <Icon name="arrow" className="h-4 w-4" />}
                </button>
              )}
            </div>

            {backendOnline && (!azureConfigured || !selectedProviderConfigured) && (
              <p role="status" className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900">
                Transcription is not available for this workspace. Contact your administrator for assistance.
              </p>
            )}
            {!backendOnline && (
              <p role="status" className="mt-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-600">
                The workspace is offline. Start the demo service, then refresh this page.
              </p>
            )}
          </section>
        </section>

        <section className="platform-map mb-6" aria-labelledby="platform-map-title">
          <div className="platform-map-header">
            <div>
              <p className="section-kicker">PLATFORM ARCHITECTURE</p>
              <h2 id="platform-map-title" className="mt-1 text-[17px] font-semibold tracking-[-0.02em] text-[#17314b]">
                A connected path from conversation to care
              </h2>
            </div>
            <span className="platform-map-note">Current demo capabilities are identified below</span>
          </div>
          <div className="platform-map-grid">
            <PlatformModule
              number="01"
              title="Capture & transcribe"
              detail="Secure audio intake, speech recognition, and speaker diarization."
              status="Current module"
              active
              icon="wave"
            />
            <PlatformModule
              number="02"
              title="Structure conversation"
              detail="Role-aware transcript reconstruction with traceable source segments."
              status="In this workflow"
              active
              icon="users"
            />
            <PlatformModule
              number="03"
              title="Clinical intelligence"
              detail="Clinical entities, evidence, uncertainty, and follow-up extraction."
              status="Platform architecture"
              icon="shield"
            />
            <PlatformModule
              number="04"
              title="Documentation & review"
              detail="Grounded SOAP drafts with clinician review and approval."
              status="Platform architecture"
              icon="file"
            />
            <PlatformModule
              number="05"
              title="Care team workspace"
              detail="Encounter records, assigned access, and operational oversight."
              status="Platform architecture"
              icon="activity"
            />
          </div>
        </section>

        <section className="workflow-card mb-6">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="section-kicker">YOUR WORKFLOW</p>
              <h2 className="mt-1 text-[17px] font-semibold tracking-[-0.02em] text-[#17314b]">This encounter’s processing path</h2>
            </div>
            <span className={`status-badge ${
              runStatus === "failed" ? "status-error" :
              runStatus === "completed" ? "status-complete" :
              processing ? "status-active" : "status-idle"
            }`}>
              {runStatus === "failed" ? "Needs attention" : runStatus === "completed" ? "Draft is ready" : processing ? "In progress" : "Ready when you are"}
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {STAGE_ORDER.map((key, index) => {
              const stage = stages[key];
              return (
                <div key={key} className={`step-card ${
                  stage.status === "in_progress" ? "step-active" :
                  stage.status === "completed" ? "step-complete" :
                  stage.status === "failed" ? "step-error" : ""
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
                    <span className={`step-icon ${
                      stage.status === "completed" ? "step-icon-complete" :
                      stage.status === "failed" ? "step-icon-error" :
                      stage.status === "in_progress" ? "step-icon-active" : ""
                    }`}>{stageIcon(key)}</span>
                  </div>
                  <div className="mt-4 text-[13px] font-semibold text-[#203e52]">{stage.label}</div>
                  <div className="mt-1 text-[11px] text-[#7b8b98]">
                    {stage.status === "waiting" ? "Up next" :
                      stage.status === "in_progress" ? "In progress" :
                        stage.status === "completed" ? "Complete" : "Needs attention"}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-5">
            <div className="mb-2 flex items-center justify-between gap-4 text-[11px]">
              <span className="truncate font-medium text-[#627788]">{currentOperation}</span>
              <span className="shrink-0 font-semibold tabular-nums text-[#264657]">{percent}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-[#eaf0f1]">
              <div
                className={`h-full rounded-full bg-gradient-to-r from-[#267c74] to-[#55b59e] transition-[width] duration-500 ${processing ? "indeterminate-track" : ""}`}
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        </section>

        <section className="activity-card">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e9eff0] px-5 py-5 sm:px-7">
            <div>
              <div className="flex items-center gap-3">
                <span className={`activity-mark ${processing ? "activity-mark-live" : ""}`}>
                  {processing ? <span className="h-2 w-2 animate-pulse rounded-full bg-white" /> : <Icon name="activity" />}
                </span>
                <div>
                  <h2 className="text-[16px] font-semibold tracking-[-0.02em] text-[#17314b]">Processing activity</h2>
                  <p className="mt-1 text-xs text-[#728391]">
                    {processing
                      ? "Your recording is being processed. Updates appear here as each step completes."
                      : "A clear record of progress will appear here."}
                  </p>
                </div>
              </div>
            </div>
            <div className="rounded-xl bg-[#f4f8f7] px-4 py-2 text-right">
              <div className="text-[9px] font-bold uppercase tracking-[0.14em] text-[#7e909a]">Elapsed time</div>
              <div className="mt-0.5 font-mono text-[15px] font-semibold tabular-nums text-[#244454]">{formatDuration(elapsedSeconds)}</div>
            </div>
          </div>
          <div className="px-5 py-4 sm:px-7">
            {currentStage && (
              <div className="mb-4 flex items-center gap-2 text-xs">
                <span className="font-medium text-[#84939d]">Current step</span>
                <span className="text-slate-300">/</span>
                <span className="font-semibold text-[#29485a]">{stages[currentStage].label}</span>
              </div>
            )}
            {streamReconnecting && processing && (
              <div className="mb-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] text-amber-800">
                Reconnecting to progress updates. Processing continues in the background.
              </div>
            )}
            {processing && elapsedSeconds >= 120 && (
              <div role="status" className="mb-3 rounded-lg bg-[#f3f8f7] px-3 py-2 text-[11px] leading-5 text-[#466b68]">
                This recording is taking longer than usual. The service is still checking for updates; please keep this page open.
              </div>
            )}
            {backendError && (
              <div role="alert" className="mb-3 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-xs leading-5 text-rose-800">
                <div className="mb-1 font-bold">We couldn’t finish this recording</div>
                {backendError}
              </div>
            )}
            <div className="scrollbar-subtle max-h-[300px] min-h-[150px] space-y-3 overflow-y-auto pr-2">
              {events.length === 0 ? (
                <div className="flex min-h-[150px] flex-col items-center justify-center text-center">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eff6f4] text-[#648d87]">
                    <Icon name="activity" className="h-5 w-5" />
                  </div>
                  <p className="mt-3 text-xs font-semibold text-[#526c78]">Ready for your recording</p>
                  <p className="mt-1 max-w-[300px] text-[11px] leading-5 text-[#8997a0]">Progress and completed steps will appear in this space.</p>
                </div>
              ) : events.map((event) => (
                <div key={event.sequence} className="flex gap-3">
                  <span className={`mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                    event.status === "failed" ? "bg-rose-100 text-rose-700" :
                    event.status === "completed" ? "bg-[#e2f3ed] text-[#287c69]" : "bg-[#eaf2f8] text-[#4c7490]"
                  }`}>
                    {event.status === "completed" ? <Icon name="check" className="h-3 w-3" /> :
                      event.status === "failed" ? <Icon name="alert" className="h-3 w-3" /> :
                        <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs leading-5 text-[#334c5c]">{event.message}</div>
                    <div className="mt-0.5 text-[10px] text-[#8997a0]">
                      {event.stage ? event.stages[event.stage]?.label : "Workflow"} <span className="px-1">·</span> {formatClock(event.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-start gap-2 border-t border-[#e9eff0] bg-[#fafcfb] px-5 py-3.5 sm:px-7">
            <Icon name="shield" className="mt-0.5 shrink-0 text-[#39877d]" />
            <p className="text-[10px] leading-4 text-[#788891]">
              This workspace supports documentation review. A clinician must verify the draft before clinical use.
            </p>
          </div>
        </section>

        {transcript && transcriptSummary && (
          <section ref={transcriptPanel} className="panel mt-6 overflow-hidden">
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line px-5 py-5 sm:px-7">
              <div>
                <div className="flex items-center gap-2">
                  <Icon name="file" className="text-teal" />
                  <h2 className="text-lg font-bold tracking-[-0.02em] text-ink">Clinical conversation transcript</h2>
                </div>
                <p className="mt-1.5 text-xs text-muted">
                  {transcript.encounter_id ? `Encounter ${transcript.encounter_id}` : "Reconstructed conversation"}
                  {" · "}Draft for clinician review
                </p>
              </div>
              <span className={`rounded-full px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.08em] ${
                transcriptSummary.needsReview ? "bg-amber-50 text-amber-800" : "bg-blue-50 text-blue-800"
              }`}>
                {transcriptSummary.needsReview ? "Review required" : "Draft · Not approved"}
              </span>
            </div>

            {transcriptSummary.needsReview && (
              <div className="mx-5 mt-5 flex gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3 sm:mx-7">
                <Icon name="alert" className="mt-0.5 shrink-0 text-amber-700" />
                <div>
                  <div className="text-xs font-bold text-amber-900">Clinician review required</div>
                  <div className="mt-1 text-[11px] leading-5 text-amber-800">
                    The final output contains review indicators. This transcript is not a diagnosis or clinician-approved record.
                  </div>
                </div>
              </div>
            )}
            {!transcriptSummary.needsReview && (
              <div className="mx-5 mt-5 flex gap-3 rounded-xl border border-blue-100 bg-blue-50/60 px-4 py-3 sm:mx-7">
                <Icon name="info" className="mt-0.5 shrink-0 text-blue" />
                <div className="text-[11px] leading-5 text-blue-900">
                  Draft transcript for clinician review. Processing completion does not indicate clinical approval.
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 px-5 py-5 sm:grid-cols-4 sm:px-7">
              <SummaryMetric label="Utterances" value={String(transcriptSummary.utterances.length)} />
              <SummaryMetric label="Participants" value={String(transcriptSummary.participantCount)} />
              <SummaryMetric label="Encounter duration" value={formatDuration(transcriptSummary.duration)} />
              <SummaryMetric label="Processing status" value={transcript.processing_status || "Available"} />
            </div>

            <div className="mx-5 mb-5 overflow-hidden rounded-xl border border-line sm:mx-7">
              <div className="grid grid-cols-[minmax(125px,0.22fr)_minmax(0,1fr)_75px] gap-3 bg-[#f7f9fc] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.1em] text-muted sm:grid-cols-[minmax(165px,0.25fr)_minmax(0,1fr)_100px]">
                <span>Participant</span>
                <span>Conversation</span>
                <span className="text-right">Duration</span>
              </div>
              <div className="scrollbar-subtle max-h-[560px] divide-y divide-line overflow-y-auto">
                {transcriptSummary.utterances.map((utterance, index) => (
                  <TranscriptRow
                    key={utterance.utterance_id || `${utterance.start_seconds ?? "time"}-${index}`}
                    utterance={utterance}
                    speakers={transcript.speaker_registry ?? []}
                    formatDuration={formatDuration}
                  />
                ))}
                {transcriptSummary.utterances.length === 0 && (
                  <div className="px-4 py-8 text-center text-xs text-muted">No utterances were present in the final output.</div>
                )}
              </div>
            </div>

            <details className="mx-5 mb-6 rounded-xl border border-line bg-[#fbfcfe] sm:mx-7">
              <summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-[#294764]">
                Inspect original final JSON
              </summary>
              <pre className="scrollbar-subtle max-h-[360px] overflow-auto border-t border-line px-4 py-4 text-[11px] leading-5 text-slate-700">
                {JSON.stringify(transcript, null, 2)}
              </pre>
            </details>
          </section>
        )}

        <footer className="mt-8 flex flex-col gap-2 border-t border-[#e2e9e9] px-1 pt-5 text-[10px] leading-5 text-[#829099] sm:flex-row sm:items-center sm:justify-between">
          <span>Ambient Clinical <span className="px-1">·</span> Conversation workspace</span>
          <span>Draft transcript only. Not a diagnosis or a substitute for clinical judgment.</span>
        </footer>
      </main>

      <VoiceAssistant backendOnline={backendOnline} onStatusChange={setVoiceStatus} />
    </div>
  );
}

function PlatformModule({
  number,
  title,
  detail,
  status,
  active = false,
  icon,
}: {
  number: string;
  title: string;
  detail: string;
  status: string;
  active?: boolean;
  icon: "wave" | "users" | "shield" | "file" | "activity";
}) {
  return (
    <article className={`platform-module ${active ? "platform-module-active" : ""}`}>
      <div className="platform-module-top">
        <span className="platform-module-number">{number}</span>
        <span className="platform-module-icon"><Icon name={icon} className="h-3.5 w-3.5" /></span>
      </div>
      <h3 className="platform-module-title">{title}</h3>
      <p className="platform-module-detail">{detail}</p>
      <span className="platform-module-status">{status}</span>
    </article>
  );
}

function TranscriptRow({
  utterance,
  speakers,
  formatDuration,
}: {
  utterance: TranscriptUtterance;
  speakers: Speaker[];
  formatDuration: (seconds: number | null) => string;
}) {
  const speaker = speakers.find(
    (item) => item.canonical_speaker_id === utterance.canonical_speaker_id,
  );
  const role = (utterance.role || speaker?.role || "UNKNOWN").toUpperCase();
  const label =
    speaker?.display_name ||
    speaker?.name ||
    utterance.canonical_speaker_id ||
    "Unidentified participant";
  const start = formatTime(utterance.start_seconds);
  const end = formatTime(utterance.end_seconds);
  const duration =
    typeof utterance.duration_seconds === "number"
      ? utterance.duration_seconds
      : typeof utterance.start_seconds === "number" && typeof utterance.end_seconds === "number"
        ? utterance.end_seconds - utterance.start_seconds
        : null;

  return (
    <article className="grid grid-cols-[minmax(125px,0.22fr)_minmax(0,1fr)_75px] items-start gap-3 px-4 py-4 sm:grid-cols-[minmax(165px,0.25fr)_minmax(0,1fr)_100px]">
      <div className="min-w-0">
        <span className={`inline-flex max-w-full items-center rounded-full px-2.5 py-1 text-[9px] font-bold tracking-[0.04em] ring-1 ring-inset ${ROLE_STYLES[role] || ROLE_STYLES.UNKNOWN}`}>
          <span className="truncate">{role.replace(/_/g, " ")}</span>
        </span>
        <div className="mt-1.5 truncate text-[10px] text-muted" title={label}>{label}</div>
        <div className="mt-1 text-[10px] tabular-nums text-slate-400">{start}{end !== "—" ? ` – ${end}` : ""}</div>
      </div>
      <p className="m-0 whitespace-pre-wrap break-words text-xs leading-6 text-[#29415a]">
        {utterance.text || "No transcript text available."}
      </p>
      <div className="pt-1 text-right text-[11px] tabular-nums text-muted">{formatDuration(duration)}</div>
    </article>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-[#fbfcfe] px-3.5 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted">{label}</div>
      <div className="mt-1.5 truncate text-sm font-bold text-ink" title={value}>{value}</div>
    </div>
  );
}

function ConnectionPill({ good, label }: { good: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-[#e1e9e7] bg-white px-3.5 py-2 shadow-[0_2px_8px_rgba(27,63,70,0.04)]">
      <span className={`h-2 w-2 rounded-full ${good ? "bg-[#35a184]" : "bg-[#d19b54]"}`} />
      <span className="text-[10px] font-semibold text-[#526c78]">{label}</span>
    </div>
  );
}

function Icon({
  name,
  className = "",
}: {
  name: "check" | "alert" | "upload" | "wave" | "users" | "file" | "mic" | "play" | "refresh" | "activity" | "shield" | "info" | "close" | "arrow";
  className?: string;
}) {
  const paths: Record<typeof name, string> = {
    check: "M5 12.5 9.2 17 19 7",
    alert: "M12 8v4m0 4h.01M10.3 3.8 2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0Z",
    upload: "M12 16V4m0 0L7 9m5-5 5 5M4 16v4h16v-4",
    wave: "M2 12h3l3-8 5 16 3-8h6",
    users: "M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2m6-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm6-7.5a4 4 0 0 1 0 7.8M20 21v-2a4 4 0 0 0-3-3.9",
    file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Zm0 0v6h6M8 13h8m-8 4h8",
    mic: "M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Zm7 10a7 7 0 0 1-14 0m7 7v3m-4 0h8",
    play: "m8 5 12 7-12 7V5Z",
    refresh: "M20 7v5h-5M4 17v-5h5m-4.1-3a7 7 0 0 1 11.6-2.5L20 12M4 12l3.5 5.5A7 7 0 0 0 19 15",
    activity: "M3 12h4l3-8 4 16 3-8h4",
    shield: "M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Zm-3-11 2 2 4-4",
    info: "M12 16v-4m0-4h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z",
    close: "m6 6 12 12M18 6 6 18",
    arrow: "M5 12h14m-6-6 6 6-6 6",
  };
  return (
    <svg
      className={`h-4 w-4 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
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
