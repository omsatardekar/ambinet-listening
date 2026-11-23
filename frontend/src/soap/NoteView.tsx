import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import {
  BookOpen, CalendarClock, Check, ClipboardList, Copy, Download, FileSignature, FlaskConical, HeartPulse, Pill, Share2, ShieldAlert, ShieldCheck, Stethoscope,
  TriangleAlert, type LucideIcon,
} from "lucide-react";
import type { Medication, PlanItem, Problem, SoapNote, SoapResult } from "./types";

/* ---------- small helpers ------------------------------------------------------------------------------------------------------------ */

const Nd = () => <span className="italic text-slate-500">Not documented</span>;
const has = (s?: string) => !!s && s.trim().length > 0;
const unverified = (s?: string) => !!s && /unverified/i.test(s);
const cap = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

const LETTER: Record<string, string> = {
  cyan: "from-cyan-300/30 to-cyan-500/10 text-cyan-100 ring-cyan-300/40",
  mint: "from-emerald-300/30 to-emerald-500/10 text-emerald-100 ring-emerald-300/40",
  violet: "from-violet-300/30 to-violet-500/10 text-violet-100 ring-violet-300/40",
  amber: "from-amber-300/30 to-amber-500/10 text-amber-100 ring-amber-300/40",
};
const RAIL_ON: Record<string, string> = { cyan: "text-cyan-200 ring-cyan-300/50 bg-cyan-400/10", mint: "text-emerald-200 ring-emerald-300/50 bg-emerald-400/10", violet: "text-violet-200 ring-violet-300/50 bg-violet-400/10", amber: "text-amber-200 ring-amber-300/50 bg-amber-400/10" };

function Band({ id, letter, title, caption, tone, children }: { id: string; letter: string; title: string; caption: string; tone: keyof typeof LETTER; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <header className="mb-6 flex items-center gap-4">
        <span className={`grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br font-display text-3xl font-bold ring-1 ${LETTER[tone]}`}>{letter}</span>
        <div><h3 className="font-display text-xl font-semibold tracking-tight text-white">{title}</h3><p className="text-sm text-slate-400">{caption}</p></div>
        <span className="h-px flex-1 bg-gradient-to-r from-white/25 to-transparent" aria-hidden />
      </header>
      <div className="grid gap-7 lg:pl-[72px]">{children}</div>
    </section>
  );
}

const Sub = ({ children, icon: Icon }: { children: ReactNode; icon?: LucideIcon }) => (
  <h4 className="mb-2.5 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">{Icon && <Icon className="h-3.5 w-3.5" aria-hidden />}{children}</h4>
);

function Bullets({ items, tone = "slate" }: { items: string[]; tone?: "slate" | "rose" | "mint" | "amber" }) {
  if (!items.length) return <p className="text-sm"><Nd /></p>;
  const dot = { slate: "bg-slate-400", rose: "bg-rose-400", mint: "bg-emerald-400", amber: "bg-amber-400" }[tone];
  return (
    <ul className="grid gap-1.5">
      {items.map((t, i) => (
        <li key={i} className="flex gap-3 text-[15px] leading-relaxed text-slate-100"><span className={`mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} aria-hidden /><span>{t}{unverified(t) && ""}</span></li>
      ))}
    </ul>
  );
}

const STATUS_TONE: Record<string, string> = {
  taking: "bg-violet-400/10 text-violet-200 ring-violet-300/30", "started today": "bg-cyan-400/10 text-cyan-200 ring-cyan-300/30", "stopped by patient": "bg-slate-400/10 text-slate-300 ring-slate-300/20",
  "stopped by clinician": "bg-slate-400/10 text-slate-300 ring-slate-300/20", "as needed": "bg-sky-400/10 text-sky-200 ring-sky-300/30", "advised against": "bg-rose-400/10 text-rose-200 ring-rose-300/30",
  unclear: "bg-amber-400/10 text-amber-200 ring-amber-300/30",
};
const Pill2 = ({ text, cls }: { text: string; cls: string }) => <span className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-medium first-letter:uppercase ring-1 ${cls}`}>{text}</span>;

/* ---------- header, navigation, tools ------------------------------------------------------------------------------------------------- */

function MetaItem({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-[11px] uppercase tracking-wider text-slate-500">{label}</dt><dd className="mt-0.5 text-sm text-slate-100">{has(value) ? value : <Nd />}</dd></div>;
}

function Tools({ markdown, encounter }: { markdown: string; encounter: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(markdown); setCopied(true); window.setTimeout(() => setCopied(false), 1800); } catch { /* clipboard blocked: the download still works */ }
  };
  const download = () => {
    const url = URL.createObjectURL(new Blob([markdown.replace(/\*\*/g, "").replace(/^#+\s*/gm, "")], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = `soap-note-${encounter || "encounter"}.txt`; a.click();
    URL.revokeObjectURL(url);
  };
  const btn = "inline-flex items-center gap-2 rounded-full bg-white/[0.07] px-4 py-2 text-sm font-medium text-slate-100 ring-1 ring-white/15 transition hover:bg-white/[0.12]";
  return (
    <div className="flex flex-wrap gap-2">
      <button type="button" onClick={copy} className={btn}>{copied ? <Check className="h-4 w-4 text-emerald-300" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}{copied ? "Copied" : "Copy note"}</button>
      <button type="button" onClick={download} className={btn}><Download className="h-4 w-4" aria-hidden />Download</button>
    </div>
  );
}

const RAIL: { id: string; letter: string; label: string; tone: keyof typeof LETTER }[] = [
  { id: "soap-s", letter: "S", label: "Subjective", tone: "cyan" }, { id: "soap-o", letter: "O", label: "Objective", tone: "mint" },
  { id: "soap-a", letter: "A", label: "Assessment", tone: "violet" }, { id: "soap-p", letter: "P", label: "Plan", tone: "amber" },
];

function Rail({ active, setActive }: { active: string; setActive: (id: string) => void }) {
  const go = (id: string) => { setActive(id); document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" }); };
  return (
    <nav aria-label="Note sections" className="sticky top-3 z-30 flex gap-2 overflow-x-auto rounded-full bg-[#0a0f1f]/85 p-1.5 ring-1 ring-white/10 backdrop-blur-md lg:top-6 lg:flex-col lg:self-start lg:rounded-3xl lg:p-2">
      {[...RAIL, { id: "soap-review", letter: "✓", label: "Review", tone: "amber" as const }].map((r) => (
        <button key={r.id} type="button" onClick={() => go(r.id)} aria-label={r.label}
          className={`flex items-center gap-2 whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium ring-1 transition lg:w-[78px] lg:flex-col lg:gap-0.5 lg:rounded-2xl lg:py-2.5 ${active === r.id ? RAIL_ON[r.tone] : "text-slate-400 ring-transparent hover:bg-white/[0.06] hover:text-white"}`}>
          <span className="font-display text-base font-bold lg:text-xl">{r.letter}</span><span className="text-[10px] uppercase tracking-wider">{r.label}</span>
        </button>
      ))}
    </nav>
  );
}

/* ---------- S ---------------------------------------------------------------------------------------------------------------------------- */

const OLDCARTS: [string, string][] = [["onset", "Onset"], ["location", "Location"], ["duration", "Duration"], ["character", "Character"], ["aggravating", "Aggravating"], ["alleviating", "Alleviating"], ["timing", "Timing"], ["severity", "Severity"], ["associated", "Associated"]];

function Medications({ meds }: { meds: Medication[] }) {
  if (!meds.length) return <p className="text-sm"><Nd /></p>;
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead><tr className="border-b border-white/15 text-[11px] uppercase tracking-wider text-slate-400">{["Medicine", "Dose", "Route", "Frequency", "Status"].map((h) => <th key={h} className="px-3 pb-2 font-semibold">{h}</th>)}</tr></thead>
        <tbody>
          {meds.map((m, i) => (
            <tr key={i} className="border-b border-white/[0.07] align-top last:border-0">
              <td className="px-3 py-3"><p className="font-medium text-white">{cap(m.name)}</p>{has(m.comment) && <p className="mt-0.5 max-w-xs text-xs leading-snug text-slate-400">{m.comment}</p>}</td>
              <td className="px-3 py-3 text-slate-200">{m.dose || <span className="text-slate-600">–</span>}</td>
              <td className="px-3 py-3 first-letter:uppercase text-slate-200">{m.route || <span className="text-slate-600">–</span>}</td>
              <td className="px-3 py-3 text-slate-200">{m.frequency || <span className="text-slate-600">–</span>}</td>
              <td className="px-3 py-3">{m.status ? <Pill2 text={m.status} cls={STATUS_TONE[m.status.toLowerCase()] ?? "bg-white/10 text-slate-200 ring-white/15"} /> : <span className="text-slate-600">–</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Allergies({ a }: { a: SoapNote["subjective"]["allergies"] }) {
  const reported = a.status === "reported" && a.items.length > 0;
  const none = a.status === "none_reported";
  const tone = reported ? "border-rose-400 bg-rose-500/[0.08]" : none ? "border-emerald-400 bg-emerald-500/[0.06]" : "border-slate-500/60 bg-white/[0.03]";
  return (
    <div className={`flex flex-wrap items-center gap-x-5 gap-y-2 rounded-xl border-l-4 px-5 py-3.5 ring-1 ring-white/10 ${tone}`}>
      <span className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider">
        {reported ? <ShieldAlert className="h-4 w-4 text-rose-300" aria-hidden /> : <ShieldCheck className={`h-4 w-4 ${none ? "text-emerald-300" : "text-slate-400"}`} aria-hidden />}
        <span className={reported ? "text-rose-300" : none ? "text-emerald-300" : "text-slate-400"}>Allergies</span>
      </span>
      {reported ? a.items.map((i, k) => (
        <span key={k} className="inline-flex flex-wrap items-baseline gap-2"><span className="font-display text-[15px] font-semibold text-white">{cap(i.substance)}</span>
          <span className="text-xs text-slate-300">{has(i.reaction) ? `reaction: ${i.reaction}` : "reaction not documented"}</span>{has(i.comment) && <span className="text-xs text-slate-400">({i.comment})</span>}</span>
      )) : <span className="text-sm text-slate-300">{none ? "No known allergies reported" : <Nd />}</span>}
      {has(a.comment) && <span className="text-xs text-slate-400">{a.comment}</span>}
    </div>
  );
}

function Subjective({ s }: { s: SoapNote["subjective"] }) {
  const elements = OLDCARTS.filter(([k]) => has(s.hpi_elements[k]));
  const ros = s.review_of_systems;
  const hist: [string, string[]][] = [["Past medical", s.past_medical_history], ["Past surgical", s.past_surgical_history], ["Family", s.family_history], ["Social", s.social_history]];
  const rosLine = (i: { system: string; finding: string }) => (i.system ? `${i.system}: ${i.finding}` : i.finding);
  return (
    <Band id="soap-s" letter="S" title="Subjective" caption="What the patient and others reported" tone="cyan">
      <div>
        <Sub>Chief complaint</Sub>
        {has(s.chief_complaint) ? <p className="font-display text-2xl font-semibold leading-snug tracking-tight text-white sm:text-[28px]">{s.chief_complaint}</p> : <Nd />}
      </div>
      <div>
        <Sub>History of present illness</Sub>
        {has(s.hpi) ? <p className="max-w-3xl text-[15px] leading-7 text-slate-100">{s.hpi}</p> : <Nd />}
        {elements.length > 0 && (
          <dl className="mt-4 grid gap-x-8 gap-y-3 rounded-2xl bg-white/[0.03] p-4 ring-1 ring-white/10 sm:grid-cols-2 lg:grid-cols-3">
            {elements.map(([k, label]) => <div key={k}><dt className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300/80">{label}</dt><dd className="mt-0.5 text-sm leading-snug text-slate-200">{s.hpi_elements[k]}</dd></div>)}
          </dl>
        )}
      </div>
      <div>
        <Sub icon={ClipboardList}>Review of systems</Sub>
        <div className="grid gap-6 md:grid-cols-2">
          <div><p className="mb-2 text-xs font-medium text-rose-300">Positive</p><Bullets items={ros.positive.map(rosLine)} tone="rose" /></div>
          <div><p className="mb-2 text-xs font-medium text-emerald-300">Negative</p><Bullets items={ros.negative.map(rosLine)} tone="mint" /></div>
        </div>
        {has(ros.not_reviewed) && <p className="mt-3 text-xs text-slate-500">{ros.not_reviewed}</p>}
      </div>
      <div>
        <Sub>History</Sub>
        <dl className="overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10">
          {hist.map(([label, items]) => (
            <div key={label} className="grid border-b border-white/10 last:border-0 sm:grid-cols-[160px_1fr]">
              <dt className="bg-white/[0.025] px-5 py-3 text-sm font-medium text-slate-300">{label}</dt>
              <dd className="px-5 py-3">{items.length ? <Bullets items={items} /> : <span className="text-sm text-slate-600">—</span>}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div><Sub icon={Pill}>Medications</Sub><Medications meds={s.medications} /></div>
      <Allergies a={s.allergies} />
    </Band>
  );
}

/* ---------- O ---------------------------------------------------------------------------------------------------------------------------- */

function Objective({ o }: { o: SoapNote["objective"] }) {
  return (
    <Band id="soap-o" letter="O" title="Objective" caption="What was measured and observed" tone="mint">
      <div>
        <Sub icon={HeartPulse}>Vital signs</Sub>
        {o.vital_signs.length ? (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
            {o.vital_signs.map((v, i) => (
              <div key={i} className="rounded-2xl bg-gradient-to-br from-emerald-400/[0.10] to-white/[0.02] p-4 ring-1 ring-white/10">
                <p className="text-xs font-medium text-slate-300">{cap(v.name)}</p>
                <p className="mt-1 font-display text-3xl font-semibold tracking-tight text-white">{v.value || "–"}<span className="ml-1 text-sm font-normal text-slate-400">{v.unit}</span></p>
                {has(v.comment) && <p className={`mt-1.5 text-[11px] leading-snug ${unverified(v.comment) ? "text-amber-300" : "text-slate-400"}`}>{v.comment}</p>}
              </div>
            ))}
          </div>
        ) : <p className="text-sm"><Nd /></p>}
      </div>
      <div>
        <Sub icon={Stethoscope}>Physical examination</Sub>
        {o.physical_exam.length ? (
          <dl className="overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10">
            {o.physical_exam.map((e, i) => (
              <div key={i} className="grid border-b border-white/10 last:border-0 sm:grid-cols-[160px_1fr]">
                <dt className="bg-white/[0.025] px-5 py-3 text-sm font-medium text-slate-300">{e.system || "General"}</dt>
                <dd className="px-5 py-3 text-[15px] leading-relaxed text-slate-100">{e.finding}</dd>
              </div>
            ))}
          </dl>
        ) : <p className="text-sm"><Nd /></p>}
      </div>
      {o.diagnostics.length > 0 && (
        <div><Sub icon={FlaskConical}>Diagnostics reviewed</Sub>
          <ul className="grid gap-2">{o.diagnostics.map((d, i) => <li key={i} className="text-[15px] text-slate-100"><span className="font-medium">{d.item}</span>{d.result && <span className="text-slate-300">: {d.result}</span>}{has(d.comment) && <span className="text-xs text-slate-400"> ({d.comment})</span>}</li>)}</ul></div>
      )}
      {has(o.comment) && <p className="text-sm text-slate-400">{o.comment}</p>}
    </Band>
  );
}

/* ---------- A ---------------------------------------------------------------------------------------------------------------------------- */

function Assessment({ a }: { a: SoapNote["assessment"] }) {
  return (
    <Band id="soap-a" letter="A" title="Assessment" caption="The clinician's impression and the problem list" tone="violet">
      {has(a.summary) && <p className="max-w-3xl font-display text-xl font-medium leading-snug text-white sm:text-[22px]">{a.summary}</p>}
      <div>
        <Sub>Problem list</Sub>
        {a.problems.length === 0 ? <p className="text-sm"><Nd /></p> : (
          <ol className="grid gap-0 overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10">
            {a.problems.map((p: Problem) => (
              <motion.li key={p.number} initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="grid gap-x-5 gap-y-1 border-b border-white/10 px-5 py-5 last:border-0 sm:grid-cols-[56px_1fr]">
                <span className="font-display text-4xl font-bold leading-none text-violet-300/70">{String(p.number).padStart(2, "0")}</span>
                <div>
                  <div className="flex flex-wrap items-center gap-3">
                    <h5 className="font-display text-lg font-semibold text-white first-letter:uppercase">{p.problem}</h5>
                    {has(p.status) && <Pill2 text={p.status} cls="bg-violet-400/10 text-violet-200 ring-violet-300/30" />}
                  </div>
                  {has(p.clinician_impression) && <p className="mt-2 text-[15px] leading-relaxed text-slate-100"><span className="text-slate-400">Impression: </span>{p.clinician_impression}</p>}
                  {has(p.reasoning) && <p className="mt-1.5 max-w-3xl text-sm leading-relaxed text-slate-300">{p.reasoning}</p>}
                  {p.icd10_suggestion && (
                    <p className="mt-3 inline-flex flex-wrap items-center gap-2 rounded-lg bg-white/[0.05] px-3 py-1.5 text-xs text-slate-300 ring-1 ring-white/10" title="Suggested for the coder; not final">
                      <span className="font-semibold text-violet-200">ICD-10-CM</span><span className="font-mono text-white">{p.icd10_suggestion.code}</span><span>{p.icd10_suggestion.description}</span><span className="text-slate-500">· suggested, verify</span>
                    </p>
                  )}
                </div>
              </motion.li>
            ))}
          </ol>
        )}
      </div>
      {a.differential.length > 0 && <div><Sub>Differential</Sub><div className="flex flex-wrap gap-2">{a.differential.map((d, i) => <span key={i} className="rounded-full bg-white/[0.06] px-3 py-1.5 text-sm text-slate-200 ring-1 ring-white/10">{d}</span>)}</div></div>}
    </Band>
  );
}

/* ---------- P ---------------------------------------------------------------------------------------------------------------------------- */

const PLAN_ROWS: { key: keyof PlanItem; label: string; icon: LucideIcon }[] = [
  { key: "diagnostics", label: "Diagnostics", icon: FlaskConical }, { key: "treatment", label: "Treatment", icon: Pill },
  { key: "patient_education", label: "Patient education", icon: BookOpen }, { key: "referrals", label: "Referrals", icon: Share2 },
];

function Plan({ p, problems }: { p: SoapNote["plan"]; problems: Problem[] }) {
  const title = (n: number) => problems.find((x) => x.number === n)?.problem ?? "Problem";
  return (
    <Band id="soap-p" letter="P" title="Plan" caption="What happens next, problem by problem" tone="amber">
      {p.by_problem.length === 0 ? <p className="text-sm"><Nd /></p> : (
        <div className="grid gap-0 overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10">
          {p.by_problem.map((bp, i) => (
            <div key={i} className="border-b border-white/10 px-5 py-5 last:border-0">
              <div className="mb-3 flex items-center gap-3"><span className="font-display text-2xl font-bold text-amber-300/70">{String(bp.problem_number).padStart(2, "0")}</span><h5 className="font-display text-lg font-semibold text-white first-letter:uppercase">{title(bp.problem_number)}</h5></div>
              <div className="grid gap-4">
                {PLAN_ROWS.map(({ key, label, icon: Icon }) => {
                  const items = bp[key] as string[];
                  if (!items.length) return null;
                  return (
                    <div key={key} className="grid gap-1.5 sm:grid-cols-[170px_1fr] sm:gap-4">
                      <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-200/80"><Icon className="h-3.5 w-3.5" aria-hidden />{label}</p>
                      <Bullets items={items} tone="amber" />
                    </div>
                  );
                })}
                {has(bp.follow_up) && (
                  <div className="grid gap-1.5 sm:grid-cols-[170px_1fr] sm:gap-4">
                    <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-200/80"><CalendarClock className="h-3.5 w-3.5" aria-hidden />Follow-up</p>
                    <p className="text-[15px] text-slate-100">{bp.follow_up}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      <div className={`rounded-2xl p-5 ring-1 ${p.return_precautions.length ? "bg-amber-400/[0.08] ring-amber-300/30" : "bg-white/[0.03] ring-white/10"}`}>
        <Sub icon={TriangleAlert}>Return precautions</Sub>
        <Bullets items={p.return_precautions} tone="amber" />
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <div><Sub icon={CalendarClock}>Follow-up</Sub>{has(p.follow_up) ? <p className="text-[15px] text-slate-100">{p.follow_up}</p> : <p className="text-sm"><Nd /></p>}</div>
        {p.care_coordination.length > 0 && <div><Sub icon={Share2}>Care coordination</Sub><Bullets items={p.care_coordination} /></div>}
      </div>
    </Band>
  );
}

/* ---------- review and signature ------------------------------------------------------------------------------------------------------- */

function Review({ note, checks }: { note: SoapNote; checks: SoapResult["review"]["system_checks"] }) {
  const items = [...note.clinician_review.items_to_verify, ...checks];
  const gaps = note.clinician_review.documentation_gaps;
  return (
    <section id="soap-review" className="scroll-mt-24">
      <header className="mb-6 flex items-center gap-4">
        <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-slate-300/20 to-slate-500/5 ring-1 ring-white/25"><FileSignature className="h-6 w-6 text-slate-100" aria-hidden /></span>
        <div><h3 className="font-display text-xl font-semibold tracking-tight text-white">Before you sign</h3><p className="text-sm text-slate-400">Please confirm these points against the recording</p></div>
        <span className="h-px flex-1 bg-gradient-to-r from-white/25 to-transparent" aria-hidden />
      </header>
      <div className="grid gap-6 lg:pl-[72px]">
        {items.length > 0 ? (
          <ul className="grid gap-0 overflow-hidden rounded-2xl bg-amber-400/[0.05] ring-1 ring-amber-300/25">
            {items.map((it, i) => (
              <li key={i} className="flex gap-3 border-b border-amber-300/15 px-5 py-3.5 last:border-0"><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
                <p className="text-sm leading-relaxed text-amber-50"><span className="font-medium">{it.topic}</span><span className="text-amber-100/70"> — {it.reason}</span></p></li>
            ))}
          </ul>
        ) : <p className="rounded-2xl bg-emerald-400/[0.07] px-5 py-3.5 text-sm text-emerald-100 ring-1 ring-emerald-300/25">Nothing was flagged for verification.</p>}
        {gaps.length > 0 && (
          <div><Sub>Documentation gaps</Sub><div className="flex flex-wrap gap-2">{gaps.map((g, i) => <span key={i} className="rounded-full bg-white/[0.05] px-3 py-1 text-xs text-slate-300 ring-1 ring-white/10">{g.replace(/\.$/, "")}</span>)}</div></div>
        )}
        <div className="rounded-2xl border border-dashed border-white/20 p-5">
          <p className="text-sm italic leading-relaxed text-slate-400">{note.clinician_review.attestation}</p>
          <div className="mt-6 grid gap-6 sm:grid-cols-[1fr_180px]">
            <div className="border-t border-white/25 pt-2 text-xs text-slate-500">Clinician signature</div>
            <div className="border-t border-white/25 pt-2 text-xs text-slate-500">Date</div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------- the whole note --------------------------------------------------------------------------------------------------------------- */

export default function NoteView({ result }: { result: SoapResult }) {
  const { note, review, markdown } = result;
  const [active, setActive] = useState("soap-s");
  const e = note.encounter;
  return (
    <div className="mt-6">
      <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-cyan-400/[0.10] via-violet-500/[0.08] to-transparent ring-1 ring-white/15">
        <div className="flex flex-wrap items-start justify-between gap-4 p-6">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-300">Progress note</p>
            <h3 className="mt-1 font-display text-3xl font-semibold tracking-tight text-white">{has(e.visit_type) ? e.visit_type : "Outpatient visit"} · SOAP</h3>
            <p className="mt-2 inline-flex items-center gap-2 rounded-full bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-200 ring-1 ring-amber-300/30"><span className="h-1.5 w-1.5 rounded-full bg-amber-300" aria-hidden />Draft · pending clinician signature</p>
          </div>
          <Tools markdown={markdown} encounter={e.encounter_id} />
        </div>
        <dl className="grid gap-x-8 gap-y-4 border-t border-white/10 bg-black/10 px-6 py-5 sm:grid-cols-2 lg:grid-cols-5">
          <MetaItem label="Encounter" value={e.encounter_id} />
          <MetaItem label="Date of service" value={e.date_of_service} />
          <MetaItem label="Patient" value={e.patient_age_sex} />
          <MetaItem label="Present" value={e.participants.join(", ")} />
          <MetaItem label="Informant" value={e.informants.join(", ")} />
        </dl>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[88px_1fr]">
        <Rail active={active} setActive={setActive} />
        <div className="grid gap-14">
          <Subjective s={note.subjective} />
          <Objective o={note.objective} />
          <Assessment a={note.assessment} />
          <Plan p={note.plan} problems={note.assessment.problems} />
          <Review note={note} checks={review.system_checks} />
        </div>
      </div>
    </div>
  );
}
