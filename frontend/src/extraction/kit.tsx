import { useEffect, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Quote, Stethoscope, TriangleAlert, User, UserRound, Users, X, type LucideIcon } from "lucide-react";
import { clock, highlightTerms, ROLE_LABEL, type Tone } from "./helpers";
import type { FactEvidence, Item } from "./types";

/* ---------- small atoms -------------------------------------------------------------------------------------------------------------- */

const BADGE: Record<Tone, string> = {
  neutral: "bg-white/10 text-slate-200 ring-white/15",
  good: "bg-emerald-400/10 text-emerald-200 ring-emerald-300/30",
  warn: "bg-amber-400/10 text-amber-200 ring-amber-300/30",
  bad: "bg-rose-400/10 text-rose-200 ring-rose-300/30",
  info: "bg-cyan-400/10 text-cyan-200 ring-cyan-300/30",
  violet: "bg-violet-400/10 text-violet-200 ring-violet-300/30",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ${BADGE[tone]}`}>{children}</span>;
}

export function Chip({ icon: Icon, children }: { icon?: LucideIcon; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.06] px-2 py-1 text-xs text-slate-300 ring-1 ring-white/10">
      {Icon && <Icon className="h-3.5 w-3.5 text-slate-400" aria-hidden />}
      {children}
    </span>
  );
}

export const TONE_BOX: Record<string, string> = {
  cyan: "bg-cyan-400/15 text-cyan-200 ring-cyan-300/30",
  rose: "bg-rose-400/15 text-rose-200 ring-rose-300/30",
  violet: "bg-violet-400/15 text-violet-200 ring-violet-300/30",
  amber: "bg-amber-400/15 text-amber-200 ring-amber-300/30",
  mint: "bg-emerald-400/15 text-emerald-200 ring-emerald-300/30",
  sky: "bg-sky-400/15 text-sky-200 ring-sky-300/30",
};

export function SectionCard({ id, icon: Icon, title, count, tone = "cyan", children, className = "" }:
  { id?: string; icon: LucideIcon; title: string; count?: number; tone?: keyof typeof TONE_BOX; children: ReactNode; className?: string }) {
  return (
    <motion.section id={id} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: 0.4 }}
      className={`scroll-mt-20 rounded-3xl bg-white/[0.04] p-5 ring-1 ring-white/10 backdrop-blur ${className}`}>
      <header className="mb-4 flex items-center gap-3">
        <span className={`grid h-9 w-9 place-items-center rounded-xl ring-1 ${TONE_BOX[tone]}`}><Icon className="h-[18px] w-[18px]" aria-hidden /></span>
        <h3 className="font-display text-base font-semibold tracking-tight text-white">{title}</h3>
        {count !== undefined && <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-300">{count}</span>}
      </header>
      {children}
    </motion.section>
  );
}

/** Circular progress with a number in the middle. */
export function Ring({ value, label, size = 76 }: { value: number; label: string; size?: number }) {
  const r = (size - 10) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value));
  return (
    <div className="flex items-center gap-3" role="img" aria-label={`${label}: ${Math.round(pct * 100)} percent`}>
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
          <defs><linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#22d3ee" /><stop offset="100%" stopColor="#8b5cf6" /></linearGradient></defs>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.10)" strokeWidth="7" />
          <motion.circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="url(#ringGrad)" strokeWidth="7" strokeLinecap="round" strokeDasharray={c}
            initial={{ strokeDashoffset: c }} animate={{ strokeDashoffset: c * (1 - pct) }} transition={{ duration: 1.1, ease: "easeOut" }} />
        </svg>
        <span className="absolute inset-0 grid place-items-center font-display text-lg font-semibold text-white">{Math.round(pct * 100)}%</span>
      </div>
      <span className="max-w-[9rem] text-xs leading-snug text-slate-300">{label}</span>
    </div>
  );
}

/* ---------- the small "sources" pill under every item -------------------------------------------------------------------------------- */

export function SourceButton({ ev, onOpen, title }: { ev?: FactEvidence; onOpen: () => void; title: string }) {
  if (!ev) return null;
  const n = ev.segments.filter((s) => s.status === "resolved").length;
  const none = n === 0;
  return (
    <button type="button" onClick={onOpen} aria-label={`${none ? "No source found" : `${n} source${n === 1 ? "" : "s"}`} for ${title}`}
      className={`group inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 transition hover:scale-[1.03] focus:outline-none focus-visible:ring-2 ${
        none ? "bg-amber-400/10 text-amber-200 ring-amber-300/30 hover:bg-amber-400/20" : "bg-cyan-400/10 text-cyan-200 ring-cyan-300/30 hover:bg-cyan-400/20"}`}>
      {none ? <TriangleAlert className="h-3.5 w-3.5" aria-hidden /> : <Quote className="h-3.5 w-3.5" aria-hidden />}
      {none ? "No source found" : `${n} source${n === 1 ? "" : "s"}`}
    </button>
  );
}

/* ---------- source panel ------------------------------------------------------------------------------------------------------------- */

const ROLE_STYLE: Record<string, { icon: LucideIcon; box: string; bubble: string }> = {
  DOCTOR: { icon: Stethoscope, box: "bg-violet-400/20 text-violet-200 ring-violet-300/30", bubble: "bg-violet-400/[0.08] ring-violet-300/20" },
  PATIENT: { icon: User, box: "bg-cyan-400/20 text-cyan-200 ring-cyan-300/30", bubble: "bg-cyan-400/[0.08] ring-cyan-300/20" },
  NURSE: { icon: Activity, box: "bg-emerald-400/20 text-emerald-200 ring-emerald-300/30", bubble: "bg-emerald-400/[0.08] ring-emerald-300/20" },
  FAMILY_MEMBER: { icon: Users, box: "bg-amber-400/20 text-amber-200 ring-amber-300/30", bubble: "bg-amber-400/[0.08] ring-amber-300/20" },
  CAREGIVER: { icon: Users, box: "bg-amber-400/20 text-amber-200 ring-amber-300/30", bubble: "bg-amber-400/[0.08] ring-amber-300/20" },
};
const ROLE_DEFAULT = { icon: UserRound, box: "bg-slate-400/20 text-slate-200 ring-slate-300/30", bubble: "bg-white/[0.05] ring-white/10" };

function Highlighted({ text, terms }: { text: string; terms: string[] }) {
  if (!terms.length) return <>{text}</>;
  const rx = new RegExp(`\\b(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\w*`, "gi");
  const parts: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(rx)) {
    const i = m.index ?? 0;
    if (i > last) parts.push(text.slice(last, i));
    parts.push(<mark key={i} className="rounded bg-cyan-300/25 px-0.5 text-white">{m[0]}</mark>);
    last = i + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

/** Where in the visit the passages sit: a bar with a numbered dot per passage. */
function VisitTimeline({ ev, total }: { ev: FactEvidence; total: number }) {
  const dots = ev.segments.filter((s) => s.status === "resolved" && typeof s.start_seconds === "number");
  if (!dots.length) return null;
  return (
    <div className="rounded-2xl bg-black/20 p-4 ring-1 ring-white/10">
      <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Where in the visit</p>
      <div className="relative h-2 rounded-full bg-white/10">
        <div className="absolute inset-y-0 left-0 w-full rounded-full bg-gradient-to-r from-cyan-400/25 via-violet-400/20 to-transparent" />
        {dots.map((s, i) => (
          <motion.span key={`${String(s.segment_id)}-${i}`} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.15 + i * 0.08, type: "spring" }}
            className="absolute -top-2 grid h-6 w-6 -translate-x-1/2 place-items-center rounded-full bg-cyan-300 text-[11px] font-bold text-slate-900 shadow-glow"
            style={{ left: `${Math.min(97, Math.max(3, ((s.start_seconds ?? 0) / total) * 100))}%` }}>{i + 1}</motion.span>
        ))}
      </div>
      <div className="mt-3 flex justify-between text-[11px] text-slate-500"><span>Start</span><span>{clock(total)}</span></div>
    </div>
  );
}

export function SourcePanel({ open, onClose, title, chips, item, ev, total }:
  { open: boolean; onClose: () => void; title: string; chips: string[]; item: Item | null; ev?: FactEvidence; total: number }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const passages = (ev?.segments ?? []).filter((s) => s.status === "resolved");
  const terms = item ? highlightTerms(item.data) : [];
  const automatic = ev?.source === "backend_matched";
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label={`Sources for ${title}`}>
          <motion.div className="absolute inset-0 bg-black/60 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.aside initial={{ x: "100%" }} animate={{ x: 0 }} exit={{ x: "100%" }} transition={{ type: "spring", damping: 32, stiffness: 320 }}
            className="absolute inset-y-0 right-0 flex w-full max-w-md flex-col bg-[#0a0f1f] shadow-card ring-1 ring-white/10 sm:rounded-l-3xl">
            <header className="flex items-start gap-3 border-b border-white/10 p-5">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-cyan-400/15 text-cyan-200 ring-1 ring-cyan-300/30"><Quote className="h-5 w-5" aria-hidden /></span>
              <div className="min-w-0 flex-1">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300">Source in the conversation</p>
                <h4 className="font-display text-lg font-semibold leading-snug text-white">{title}</h4>
                {chips.length > 0 && <div className="mt-2 flex flex-wrap gap-1.5">{chips.map((c) => <Chip key={c}>{c}</Chip>)}</div>}
              </div>
              <button type="button" onClick={onClose} aria-label="Close" className="rounded-full p-2 text-slate-400 transition hover:bg-white/10 hover:text-white"><X className="h-5 w-5" /></button>
            </header>

            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {ev && <VisitTimeline ev={ev} total={total} />}
              {passages.length === 0 ? (
                <div className="rounded-2xl bg-amber-400/10 p-4 text-sm text-amber-100 ring-1 ring-amber-300/30">
                  <p className="flex items-center gap-2 font-medium"><TriangleAlert className="h-4 w-4" aria-hidden />No matching passage found</p>
                  <p className="mt-1 text-amber-100/80">Nothing in the conversation closely resembles this item. It may be a paraphrase, or it may not have been said. Please check it against the recording.</p>
                </div>
              ) : passages.map((s, i) => {
                const st = ROLE_STYLE[s.role ?? ""] ?? ROLE_DEFAULT;
                const Icon = st.icon;
                return (
                  <motion.article key={`${String(s.segment_id)}-${i}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.07 }}
                    className={`rounded-2xl p-4 ring-1 ${st.bubble}`}>
                    <div className="mb-2 flex items-center gap-2.5">
                      <span className={`grid h-8 w-8 place-items-center rounded-full ring-1 ${st.box}`}><Icon className="h-4 w-4" aria-hidden /></span>
                      <div className="leading-tight">
                        <p className="text-sm font-medium text-white">{ROLE_LABEL[s.role ?? ""] ?? "Speaker"}</p>
                        <p className="text-[11px] text-slate-400">{clock(s.start_seconds)} – {clock(s.end_seconds)}</p>
                      </div>
                      <span className="ml-auto grid h-6 w-6 place-items-center rounded-full bg-white/10 text-[11px] font-semibold text-slate-200">{i + 1}</span>
                    </div>
                    <p className="text-[15px] leading-relaxed text-slate-100"><Highlighted text={s.text ?? ""} terms={terms} /></p>
                    {s.match_score !== undefined && (
                      <div className="mt-3 flex items-center gap-2" aria-label={`Relevance ${Math.round(s.match_score * 100)} percent`}>
                        <span className="text-[11px] text-slate-400">Relevance</span>
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                          <motion.div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400" initial={{ width: 0 }} animate={{ width: `${Math.round(s.match_score * 100)}%` }} transition={{ delay: 0.3, duration: 0.7 }} />
                        </div>
                        <span className="text-[11px] font-medium text-slate-200">{Math.round(s.match_score * 100)}%</span>
                      </div>
                    )}
                  </motion.article>
                );
              })}
            </div>

            <footer className="border-t border-white/10 p-4 text-xs leading-relaxed text-slate-400">
              {automatic ? "These passages were linked automatically by comparing wording. " : ""}A linked passage is a pointer, not proof: please confirm each item against the recording.
            </footer>
          </motion.aside>
        </div>
      )}
    </AnimatePresence>
  );
}
