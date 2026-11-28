import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, FileText, Info, Link2, RefreshCw, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";
import { Badge, Chip, Ring, SourcePanel, SourceButton } from "./extraction/kit";
import { buildModel, friendlyError, friendlyNotes, labelOf, reporter, visitSeconds } from "./extraction/helpers";
import { AlertRibbon, Denied, Examination, History, Impression, Medications, Plan, Recommendations, Symptoms, Vitals } from "./extraction/sections";
import type { Ctx, Derived, Extraction, FactEvidence, JobStatus, SourceRequest } from "./extraction/types";

/**
 * Clinical summary of a finished conversation. Starts a background job, shows friendly progress, then lays the result out as a visit
 * summary (reason, impression, vitals, symptoms, history, medications, examination, plan) with a source panel for every item.
 * Nothing about how the summary is produced is shown to the user; everything is an unvalidated draft for clinician review.
 */

type Props = { runId: string | null; encounterId?: string };

const TERMINAL = ["completed", "completed_with_warnings", "failed"];

const STEPS = [
  { title: "Reading the conversation", icon: FileText, statuses: ["queued", "preparing_transcript", "loading_model", "reading_transcript"] },
  { title: "Identifying clinical details", icon: Sparkles, statuses: ["extracting"] },
  { title: "Checking the details", icon: ShieldCheck, statuses: ["validating_output"] },
  { title: "Linking sources", icon: Link2, statuses: ["resolving_evidence"] },
];

const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

/* ---------- progress ----------------------------------------------------------------------------------------------------------------- */

function Progress({ job, elapsed }: { job: JobStatus; elapsed: number }) {
  const active = Math.max(0, STEPS.findIndex((s) => s.statuses.includes(job.status)));
  return (
    <div className="mt-6" aria-live="polite">
      <ol className="grid gap-3 sm:grid-cols-4">
        {STEPS.map((s, i) => {
          const done = i < active;
          const now = i === active;
          const Icon = s.icon;
          return (
            <li key={s.title} className={`relative overflow-hidden rounded-2xl p-4 ring-1 transition ${now ? "bg-cyan-400/10 ring-cyan-300/40" : done ? "bg-emerald-400/[0.07] ring-emerald-300/25" : "bg-white/[0.03] ring-white/10"}`}>
              <div className="flex items-center gap-3">
                <span className={`relative grid h-9 w-9 place-items-center rounded-xl ring-1 ${now ? "bg-cyan-400/20 text-cyan-200 ring-cyan-300/40" : done ? "bg-emerald-400/20 text-emerald-200 ring-emerald-300/40" : "bg-white/5 text-slate-500 ring-white/10"}`}>
                  {done ? <Check className="h-4 w-4" aria-hidden /> : <Icon className="h-4 w-4" aria-hidden />}
                  {now && <span className="absolute inset-0 animate-ping rounded-xl bg-cyan-300/20" aria-hidden />}
                </span>
                <span className={`text-sm font-medium ${now ? "text-white" : done ? "text-emerald-100" : "text-slate-500"}`}>{s.title}</span>
              </div>
              {now && <span className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden"><span className="block h-full w-1/2 animate-[shimmer_1.6s_linear_infinite] bg-gradient-to-r from-transparent via-cyan-300 to-transparent" /></span>}
            </li>
          );
        })}
      </ol>
      <p className="mt-4 flex items-center gap-2 text-sm text-slate-300">
        <span className="font-medium text-white">Preparing your summary</span>
        <span className="text-slate-500">·</span>
        <span className="tabular-nums text-slate-400">{mmss(elapsed)}</span>
        <span className="hidden text-slate-500 sm:inline">· this usually takes a few minutes</span>
      </p>
      <div className="mt-6 grid gap-4 md:grid-cols-3" aria-hidden>
        {[0, 1, 2].map((i) => <div key={i} className="relative h-28 overflow-hidden rounded-2xl bg-white/[0.04] ring-1 ring-white/10"><div className="absolute inset-0 animate-[shimmer_2s_linear_infinite] bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" style={{ animationDelay: `${i * 0.25}s` }} /></div>)}
      </div>
    </div>
  );
}

/* ---------- the finished summary ----------------------------------------------------------------------------------------------------- */

const NAV: { id: string; label: string }[] = [
  { id: "vitals", label: "Vitals" }, { id: "symptoms", label: "Symptoms" }, { id: "history", label: "History" }, { id: "medications", label: "Medications" },
  { id: "examination", label: "Examination" }, { id: "assessment", label: "Impression" }, { id: "plan", label: "Plan" },
];

function Summary({ extraction, derived, job }: { extraction: Extraction; derived: Derived | null; job: JobStatus }) {
  const model = useMemo(() => buildModel(extraction), [extraction]);
  const evidence = useMemo(() => new Map<string, FactEvidence>((derived?.facts ?? []).map((f) => [f.path, f])), [derived]);
  const [source, setSource] = useState<SourceRequest | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const ctx: Ctx = useMemo(() => ({ evidence, openSource: (r) => { setSource(r); setPanelOpen(true); } }), [evidence]);
  const total = useMemo(() => visitSeconds(derived), [derived]);

  const planCount = model.tests.length + model.actions.length + model.followUp.length;
  const present: Record<string, boolean> = {
    vitals: model.vitals.length > 0, symptoms: model.symptoms.length > 0 || model.denied.length > 0,
    history: model.pmh.length + model.surgical.length + model.family.length + model.social.length > 0, medications: model.meds.length > 0,
    examination: model.exam.length + model.ros.length + model.conditions.length > 0, assessment: model.assessment.length > 0, plan: planCount > 0,
  };
  const missing = [
    ["Vital signs", model.vitals.length], ["Symptoms", model.symptoms.length], ["Medical history", model.pmh.length], ["Surgical history", model.surgical.length],
    ["Family history", model.family.length], ["Social history", model.social.length], ["Medications", model.meds.length], ["Examination", model.exam.length],
    ["Impression", model.assessment.length], ["Plan", planCount],
  ].filter(([, n]) => n === 0).map(([l]) => l as string);

  const facts = derived?.facts ?? [];
  const linked = facts.filter((f) => f.segments.some((s) => s.status === "resolved")).length;
  const notes = friendlyNotes(job.warnings);
  const took = job.started_at && job.finished_at ? Math.max(0, Math.round((Date.parse(job.finished_at) - Date.parse(job.started_at)) / 1000)) : null;
  const complaint = model.complaint;
  const complaintText = complaint ? labelOf(complaint.data) : "";
  const stats: [string, number][] = [["Symptoms", model.symptoms.length], ["Medications", model.meds.length], ["Allergies", model.allergies.length], ["Plan items", planCount]];
  const jump = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  const activeEv = source ? evidence.get(source.item.path) : undefined;

  return (
    <div className="mt-6 grid gap-5">
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-cyan-400/[0.14] via-violet-500/[0.10] to-transparent p-6 ring-1 ring-white/15">
        <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-violet-500/20 blur-3xl" aria-hidden />
        <div className="relative grid gap-6 lg:grid-cols-[1.4fr_1fr]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300">Reason for visit</p>
            {complaintText ? (
              <>
                <blockquote className="mt-2 font-display text-3xl font-semibold first-letter:uppercase leading-tight text-white">“{complaintText}”</blockquote>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {complaint && reporter(complaint.data) && <Chip>Reported by {reporter(complaint.data).toLowerCase()}</Chip>}
                  {complaint && <SourceButton ev={evidence.get(complaint.path)} title={complaintText} onOpen={() => ctx.openSource({ item: complaint, title: complaintText, chips: [] })} />}
                </div>
              </>
            ) : <p className="mt-2 font-display text-xl text-slate-300">The reason for the visit was not clearly stated.</p>}
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
            {stats.map(([label, n]) => (
              <div key={label} className="rounded-2xl bg-black/20 p-3 ring-1 ring-white/10">
                <p className="font-display text-2xl font-semibold text-white">{n}</p>
                <p className="text-xs text-slate-400">{label}</p>
              </div>
            ))}
          </div>
        </div>
        {facts.length > 0 && (
          <div className="relative mt-5 flex flex-wrap items-center gap-x-8 gap-y-3 border-t border-white/10 pt-5">
            <Ring value={linked / facts.length} label={`${linked} of ${facts.length} items linked to the conversation`} />
            <p className="max-w-md text-xs leading-relaxed text-slate-400">Open the <span className="text-cyan-200">sources</span> button on any item to see where it was said, with the speaker and time.</p>
          </div>
        )}
      </motion.div>

      <AlertRibbon allergies={model.allergies} questions={model.uncertainties} ctx={ctx} />

      <div className="sticky top-3 z-30 -mx-1 flex gap-2 overflow-x-auto rounded-full bg-[#0a0f1f]/80 p-1.5 ring-1 ring-white/10 backdrop-blur-md" role="navigation" aria-label="Summary sections">
        {NAV.filter((n) => present[n.id]).map((n) => (
          <button key={n.id} type="button" onClick={() => jump(n.id)} className="whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10 hover:text-white">{n.label}</button>
        ))}
      </div>

      {model.assessment.length > 0 && <Impression items={model.assessment} ctx={ctx} />}
      {model.vitals.length > 0 && <Vitals items={model.vitals} ctx={ctx} />}
      {model.symptoms.length > 0 && <Symptoms items={model.symptoms} ctx={ctx} />}
      {model.denied.length > 0 && <Denied items={model.denied} ctx={ctx} />}
      <History pmh={model.pmh} surgical={model.surgical} family={model.family} social={model.social} ctx={ctx} />
      {model.meds.length > 0 && <Medications items={model.meds} ctx={ctx} />}
      <Examination exam={model.exam} ros={model.ros} conditions={model.conditions} ctx={ctx} />
      <Plan tests={model.tests} actions={model.actions} followUp={model.followUp} ctx={ctx} />
      <Recommendations items={model.recommendations} total={model.recommendationsTotal} ctx={ctx} />

      {missing.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl bg-white/[0.03] p-4 ring-1 ring-white/10">
          <Info className="h-4 w-4 text-slate-400" aria-hidden />
          <span className="mr-1 text-sm text-slate-300">Not discussed in this conversation:</span>
          {missing.map((m) => <span key={m} className="rounded-full bg-white/[0.06] px-2.5 py-1 text-xs text-slate-400 ring-1 ring-white/10">{m}</span>)}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
        {job.saved_to && <span className="inline-flex items-center gap-1.5 text-emerald-300"><Check className="h-3.5 w-3.5" aria-hidden />Saved to the patient record</span>}
        {took !== null && <span>Prepared in {took >= 60 ? `${Math.floor(took / 60)} min ${took % 60} s` : `${took} s`}</span>}
        <Badge tone="warn">Draft · clinician review required</Badge>
      </div>
      {notes.map((n) => (
        <p key={n} className="flex items-center gap-2 rounded-xl bg-amber-400/10 p-3 text-xs text-amber-100 ring-1 ring-amber-300/25"><TriangleAlert className="h-4 w-4 shrink-0" aria-hidden />{n}</p>
      ))}

      <SourcePanel open={panelOpen} onClose={() => setPanelOpen(false)} title={source?.title ?? ""} chips={source?.chips ?? []} item={source?.item ?? null} ev={activeEv} total={total} />
    </div>
  );
}

/* ---------- container ---------------------------------------------------------------------------------------------------------------- */

export default function ExtractionPanel({ runId, encounterId }: Props) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extraction, setExtraction] = useState<Extraction | null>(null);
  const [derived, setDerived] = useState<Derived | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const source = useRef<EventSource | null>(null);

  const loadResult = useCallback(async (jobId: string) => {
    const [r, e] = await Promise.all([fetch(`/api/extraction/${jobId}/result`), fetch(`/api/extraction/${jobId}/evidence`)]);
    if (!r.ok) { setError("The summary is not available yet. Please try again."); return; }
    const body = await r.json();
    setExtraction(body.extraction);
    if (e.ok) setDerived(await e.json());
  }, []);

  const follow = useCallback((jobId: string) => {
    source.current?.close();
    const es = new EventSource(`/api/extraction/${jobId}/events`);
    source.current = es;
    const refresh = async () => {
      const s = await fetch(`/api/extraction/${jobId}/status`);
      if (!s.ok) return;
      const status: JobStatus = await s.json();
      setJob(status);
      if (TERMINAL.includes(status.status)) { es.close(); if (status.status !== "failed") await loadResult(jobId); }
    };
    es.onmessage = () => { void refresh(); };
    es.onerror = () => { void refresh(); };
    void refresh();
  }, [loadResult]);

  useEffect(() => () => source.current?.close(), []);
  useEffect(() => {
    if (!job || TERMINAL.includes(job.status) || !job.started_at) return;
    const t0 = Date.parse(job.started_at);
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - t0) / 1000)));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [job]);

  const start = async () => {
    setError(null); setExtraction(null); setDerived(null); setJob(null);
    const body = runId ? { run_id: runId } : { encounter_id: encounterId };
    const r = await fetch("/api/extraction/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { setError(friendlyError(j.code)); return; }
    follow(j.job_id);
  };

  const running = !!job && !TERMINAL.includes(job.status);
  const failed = job?.status === "failed";

  return (
    <section className="mt-10 rounded-[2rem] bg-white/[0.04] p-6 text-slate-100 ring-1 ring-white/10 sm:p-8" aria-label="Clinical summary">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400/30 to-violet-500/30 text-cyan-100 ring-1 ring-white/20"><Sparkles className="h-5 w-5" aria-hidden /></span>
            <div>
              <h2 className="font-display text-2xl font-semibold tracking-tight text-white">Clinical summary</h2>
              <p className="text-sm text-slate-400">The key clinical details from this conversation, with their sources.</p>
            </div>
          </div>
        </div>
        <button type="button" onClick={start} disabled={running || (!runId && !encounterId)}
          className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-glow transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
          {job ? <RefreshCw className={`h-4 w-4 ${running ? "animate-spin" : ""}`} aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
          {running ? "Preparing…" : job ? "Regenerate summary" : "Generate summary"}
        </button>
      </div>

      <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-amber-200/80"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />Prepared automatically from the conversation. It can miss or misstate details, so please review it before use. It is not a diagnosis or an order.</p>

      <AnimatePresence mode="wait">
        {(error || failed) && (
          <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} role="alert" className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-500/10 p-4 text-sm text-rose-100 ring-1 ring-rose-400/30">
            <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-300" aria-hidden />
            <div>
              <p className="font-medium">{error ?? friendlyError(job?.error?.code)}</p>
              {job && <p className="mt-1 text-xs text-rose-200/60">Reference {job.job_id.slice(0, 8)}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!job && !error && (
        <div className="mt-6 grid place-items-center rounded-3xl border border-dashed border-white/15 bg-white/[0.02] px-6 py-14 text-center">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-cyan-400/10 text-cyan-200 ring-1 ring-cyan-300/30"><FileText className="h-6 w-6" aria-hidden /></span>
          <p className="mt-4 font-display text-lg font-semibold text-white">Turn this conversation into a clinical summary</p>
          <p className="mt-1 max-w-md text-sm text-slate-400">Vitals, symptoms, history, medications, impression and plan, each linked back to what was said.</p>
        </div>
      )}

      {job && running && <Progress job={job} elapsed={elapsed} />}
      {job && !running && !failed && extraction && <Summary extraction={extraction} derived={derived} job={job} />}
    </section>
  );
}

