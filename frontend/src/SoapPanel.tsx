import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Check, ClipboardList, FileText, Info, RefreshCw, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";
import NoteView from "./soap/NoteView";
import type { SoapJob, SoapResult } from "./soap/types";

/**
 * SOAP note: the last step. Starts a background job that turns the saved clinical summary into a SOAP progress note, shows plain progress, then lays the
 * note out as a clinical document. Nothing about how the note is written is shown; it is a draft for clinician review.
 */

type Props = { runId: string | null; encounterId?: string };

const TERMINAL = ["completed", "completed_with_warnings", "failed"];
const STEPS = [
  { title: "Reading the clinical summary", icon: FileText, statuses: ["queued", "reading_summary"] },
  { title: "Drafting the note", icon: Sparkles, statuses: ["drafting_note"] },
  { title: "Checking the details", icon: ShieldCheck, statuses: ["checking_note"] },
  { title: "Saving the note", icon: Check, statuses: ["saving"] },
];

const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

function friendlyError(code?: string, message?: string): string {
  switch (code) {
    case "extraction_not_found": case "extraction_read_failed": return "There is no clinical summary for this conversation yet. Please generate the clinical summary first, then try again.";
    case "run_not_ready": return "The conversation is not ready yet. Please finish the transcription first.";
    case "no_findings": return "The clinical summary has no findings to write a note from.";
    case "note_format": return "The note could not be completed this time. Please try again.";
    case "storage_not_configured": case "agent_not_configured": case "agent_version_missing": case "model_not_configured": case "agent_sdk_missing": case "instructions_missing": return "The SOAP note service is not available right now. Please contact support.";
    default: return message && /clinical summary|conversation/i.test(message) && !/model|agent|endpoint|azure/i.test(message) ? message : "We could not prepare the SOAP note this time. Please try again.";
  }
}

function Progress({ job, elapsed }: { job: SoapJob; elapsed: number }) {
  const active = Math.max(0, STEPS.findIndex((s) => s.statuses.includes(job.status)));
  return (
    <div className="mt-6" aria-live="polite">
      <ol className="grid gap-3 sm:grid-cols-4">
        {STEPS.map((s, i) => {
          const done = i < active, now = i === active, Icon = s.icon;
          return (
            <li key={s.title} className={`relative overflow-hidden rounded-2xl p-4 ring-1 transition ${now ? "bg-violet-400/10 ring-violet-300/40" : done ? "bg-emerald-400/[0.07] ring-emerald-300/25" : "bg-white/[0.03] ring-white/10"}`}>
              <div className="flex items-center gap-3">
                <span className={`relative grid h-9 w-9 place-items-center rounded-xl ring-1 ${now ? "bg-violet-400/20 text-violet-200 ring-violet-300/40" : done ? "bg-emerald-400/20 text-emerald-200 ring-emerald-300/40" : "bg-white/5 text-slate-500 ring-white/10"}`}>
                  {done ? <Check className="h-4 w-4" aria-hidden /> : <Icon className="h-4 w-4" aria-hidden />}
                  {now && <span className="absolute inset-0 animate-ping rounded-xl bg-violet-300/20" aria-hidden />}
                </span>
                <span className={`text-sm font-medium ${now ? "text-white" : done ? "text-emerald-100" : "text-slate-500"}`}>{s.title}</span>
              </div>
              {now && <span className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden"><span className="block h-full w-1/2 animate-[shimmer_1.6s_linear_infinite] bg-gradient-to-r from-transparent via-violet-300 to-transparent" /></span>}
            </li>
          );
        })}
      </ol>
      <p className="mt-4 flex items-center gap-2 text-sm text-slate-300"><span className="font-medium text-white">Writing your note</span><span className="text-slate-500">·</span><span className="tabular-nums text-slate-400">{mmss(elapsed)}</span><span className="hidden text-slate-500 sm:inline">· usually one to two minutes</span></p>
      <div className="mt-6 grid gap-3" aria-hidden>
        {[0, 1, 2].map((i) => <div key={i} className="relative h-16 overflow-hidden rounded-2xl bg-white/[0.04] ring-1 ring-white/10"><div className="absolute inset-0 animate-[shimmer_2s_linear_infinite] bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" style={{ animationDelay: `${i * 0.25}s` }} /></div>)}
      </div>
    </div>
  );
}

export default function SoapPanel({ runId, encounterId }: Props) {
  const [job, setJob] = useState<SoapJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SoapResult | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const source = useRef<EventSource | null>(null);
  const timer = useRef<number | null>(null);

  const stop = useCallback(() => { source.current?.close(); source.current = null; if (timer.current) { window.clearInterval(timer.current); timer.current = null; } }, []);

  const loadResult = useCallback(async (jobId: string) => {
    const r = await fetch(`/api/soap/${jobId}/result`);
    if (!r.ok) { setError("The SOAP note is not available yet. Please try again."); return; }
    setResult(await r.json());
  }, []);

  const follow = useCallback((jobId: string) => {
    stop();
    let finished = false;
    const refresh = async () => {
      if (finished) return;
      const s = await fetch(`/api/soap/${jobId}/status`).catch(() => null);
      if (!s || !s.ok) return;
      const status: SoapJob = await s.json();
      setJob(status);
      if (TERMINAL.includes(status.status)) { finished = true; stop(); if (status.status !== "failed") await loadResult(jobId); }
    };
    try { const es = new EventSource(`/api/soap/${jobId}/events`); source.current = es; es.onmessage = () => { void refresh(); }; es.onerror = () => { void refresh(); }; } catch { /* polling below covers it */ }
    timer.current = window.setInterval(() => { void refresh(); }, 3000);
    void refresh();
  }, [loadResult, stop]);

  useEffect(() => stop, [stop]);
  useEffect(() => {
    if (!job || TERMINAL.includes(job.status) || !job.started_at) return;
    const t0 = Date.parse(job.started_at);
    const tick = () => setElapsed(Math.max(0, Math.floor((Date.now() - t0) / 1000)));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [job]);

  const start = async () => {
    setError(null); setResult(null); setJob(null);
    const body = runId ? { run_id: runId } : { encounter_id: encounterId };
    const r = await fetch("/api/soap/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { setError(friendlyError(undefined, typeof j.detail === "string" ? j.detail : undefined)); return; }
    follow(j.job_id);
  };

  const running = !!job && !TERMINAL.includes(job.status);
  const failed = job?.status === "failed";
  const took = job?.started_at && job.finished_at ? Math.max(0, Math.round((Date.parse(job.finished_at) - Date.parse(job.started_at)) / 1000)) : null;

  return (
    <section className="mt-10 rounded-[2rem] bg-white/[0.04] p-6 text-slate-100 ring-1 ring-white/10 sm:p-8" aria-label="SOAP note">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-400/30 to-amber-400/25 text-violet-100 ring-1 ring-white/20"><ClipboardList className="h-5 w-5" aria-hidden /></span>
          <div>
            <h2 className="font-display text-2xl font-semibold tracking-tight text-white">SOAP note</h2>
            <p className="text-sm text-slate-400">A structured progress note for this visit, ready for clinician review.</p>
          </div>
        </div>
        <button type="button" onClick={start} disabled={running || (!runId && !encounterId)}
          className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-400 to-amber-300 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-glow transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
          {job ? <RefreshCw className={`h-4 w-4 ${running ? "animate-spin" : ""}`} aria-hidden /> : <Sparkles className="h-4 w-4" aria-hidden />}
          {running ? "Writing…" : job ? "Regenerate note" : "Generate SOAP note"}
        </button>
      </div>

      <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-amber-200/80"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />Prepared automatically from the clinical summary. It can miss or misstate details and is not part of the medical record until a clinician has reviewed, edited and signed it.</p>

      <AnimatePresence mode="wait">
        {(error || failed) && (
          <motion.div key="err" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} role="alert" className="mt-5 flex items-start gap-3 rounded-2xl bg-rose-500/10 p-4 text-sm text-rose-100 ring-1 ring-rose-400/30">
            <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-300" aria-hidden />
            <div><p className="font-medium">{error ?? friendlyError(job?.error?.code, job?.error?.message)}</p>{job && <p className="mt-1 text-xs text-rose-200/60">Reference {job.job_id.slice(0, 8)}</p>}</div>
          </motion.div>
        )}
      </AnimatePresence>

      {!job && !error && (
        <div className="mt-6 grid place-items-center rounded-3xl border border-dashed border-white/15 bg-white/[0.02] px-6 py-14 text-center">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-violet-400/10 text-violet-200 ring-1 ring-violet-300/30"><ClipboardList className="h-6 w-6" aria-hidden /></span>
          <p className="mt-4 font-display text-lg font-semibold text-white">Turn the clinical summary into a SOAP note</p>
          <p className="mt-1 max-w-lg text-sm text-slate-400">Subjective, Objective, Assessment and Plan, written problem by problem, with the points that need your confirmation listed before you sign.</p>
        </div>
      )}

      {job && running && <Progress job={job} elapsed={elapsed} />}
      {job && !running && !failed && result && (
        <>
          <NoteView result={result} />
          <div className="mt-8 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500">
            {job.saved_to && <span className="inline-flex items-center gap-1.5 text-emerald-300"><Check className="h-3.5 w-3.5" aria-hidden />Saved to the patient record</span>}
            {took !== null && <span>Prepared in {took >= 60 ? `${Math.floor(took / 60)} min ${took % 60} s` : `${took} s`}</span>}
            {job.warnings.some((w) => /conversation could not be read/i.test(w)) && <span className="inline-flex items-center gap-1.5 text-amber-200"><TriangleAlert className="h-3.5 w-3.5" aria-hidden />The full conversation could not be read, so statements about what was not discussed may be incomplete.</span>}
            {job.warnings.some((w) => /could not be saved/i.test(w)) && <span className="inline-flex items-center gap-1.5 text-amber-200"><TriangleAlert className="h-3.5 w-3.5" aria-hidden />The note could not be saved to the patient record. It is shown here only.</span>}
          </div>
        </>
      )}
    </section>
  );
}
