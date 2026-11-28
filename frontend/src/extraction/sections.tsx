import { motion } from "framer-motion";
import type { ReactNode } from "react";
import {
  Activity, Ban, Bone, CalendarClock, Check, CircleHelp, ClipboardList, Clock, Lightbulb, Droplets, FlaskConical, Gauge, HeartPulse, Home, MapPin, Pill, Repeat, Ruler,
  Scale, ScanLine, ShieldAlert, ShieldCheck, Stethoscope, Thermometer, Users, Wind, type LucideIcon,
} from "lucide-react";
import { Badge, Chip, SectionCard, SourceButton, TONE_BOX } from "./kit";
import { human, labelOf, list, pick, reporter, statusOf } from "./helpers";
import type { Ctx, Item, Rec } from "./types";

/** The "N sources" pill of one item. */
function Src({ ctx, item, title, chips }: { ctx: Ctx; item: Item; title: string; chips: string[] }) {
  return <SourceButton ev={ctx.evidence.get(item.path)} title={title} onOpen={() => ctx.openSource({ item, title, chips })} />;
}

const by = (d: Rec) => (reporter(d) ? `Reported by ${reporter(d).toLowerCase()}` : "");

/* ---------- vitals ------------------------------------------------------------------------------------------------------------------- */

function vitalIcon(name: string): LucideIcon {
  const n = name.toLowerCase();
  if (/temp/.test(n)) return Thermometer;
  if (/pressure|bp/.test(n)) return Gauge;
  if (/heart|pulse/.test(n)) return HeartPulse;
  if (/oxygen|spo|saturation/.test(n)) return Droplets;
  if (/resp|breath/.test(n)) return Wind;
  if (/weight/.test(n)) return Scale;
  if (/height|bmi/.test(n)) return Ruler;
  return Activity;
}

export function Vitals({ items, ctx }: { items: Item[]; ctx: Ctx }) {
  return (
    <SectionCard id="vitals" icon={HeartPulse} title="Vital signs" count={items.length} tone="cyan">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
        {items.map((it, i) => {
          const name = human(pick(it.data, "name", "normalized_name")) || "Measurement";
          const value = pick(it.data, "value");
          const unit = pick(it.data, "unit");
          const Icon = vitalIcon(name);
          return (
            <motion.div key={it.path} initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
              className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-cyan-400/[0.12] to-white/[0.02] p-4 ring-1 ring-white/10">
              <span className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-cyan-400/10 text-cyan-300 ring-1 ring-cyan-300/25"><Icon className="h-[18px] w-[18px]" aria-hidden /></span>
              <p className="pr-11 text-xs font-medium text-slate-300">{name}</p>
              <p className="mt-1 font-display text-3xl font-semibold tracking-tight text-white">{value || "–"}<span className="ml-1 text-sm font-normal text-slate-400">{unit}</span></p>
              <div className="mt-3"><Src ctx={ctx} item={it} title={`${name} ${value} ${unit}`.trim()} chips={[by(it.data)].filter(Boolean)} /></div>
            </motion.div>
          );
        })}
      </div>
    </SectionCard>
  );
}

/* ---------- shared pieces of the flat layout ----------------------------------------------------------------------------------------- */

/** Section title without a box: icon, title, count and a fading rule. */
function FlatHeader({ id, icon: Icon, title, count, tone = "cyan" }: { id?: string; icon: LucideIcon; title: string; count?: number; tone?: keyof typeof TONE_BOX }) {
  return (
    <div id={id} className="mb-3 flex scroll-mt-20 items-center gap-3">
      <span className={`grid h-8 w-8 place-items-center rounded-lg ring-1 ${TONE_BOX[tone]}`}><Icon className="h-4 w-4" aria-hidden /></span>
      <h3 className="font-display text-base font-semibold tracking-tight text-white">{title}</h3>
      {count !== undefined && <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-300">{count}</span>}
      <span className="h-px flex-1 bg-gradient-to-r from-white/25 to-transparent" aria-hidden />
    </div>
  );
}

/** Small icon + text, no box. */
function Meta({ icon: Icon, children }: { icon?: LucideIcon; children: ReactNode }) {
  return <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">{Icon && <Icon className="h-3.5 w-3.5 text-slate-500" aria-hidden />}{children}</span>;
}

const PANEL = "overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10";
const DOT: Record<string, string> = { good: "bg-emerald-400", warn: "bg-amber-400", bad: "bg-rose-400", info: "bg-cyan-400", violet: "bg-violet-400", neutral: "bg-slate-400" };

function StatusDot({ raw }: { raw: unknown }) {
  const st = statusOf(raw);
  if (!st) return null;
  return <span className="inline-flex items-center gap-1.5 text-xs text-slate-300"><span className={`h-1.5 w-1.5 rounded-full ${DOT[st.tone]}`} aria-hidden />{st.label}</span>;
}

/* ---------- allergies and open questions: one slim ribbon ----------------------------------------------------------------------------- */

export function AlertRibbon({ allergies, questions, ctx }: { allergies: Item[]; questions: Item[]; ctx: Ctx }) {
  const has = allergies.length > 0;
  return (
    <div id="allergies" className="flex scroll-mt-20 flex-col overflow-hidden rounded-2xl bg-white/[0.03] ring-1 ring-white/10 lg:flex-row">
      <div className={`flex flex-wrap items-center gap-x-4 gap-y-2 border-l-4 px-5 py-3.5 ${has ? "border-rose-400 bg-rose-500/[0.07]" : "border-slate-500/60"}`}>
        <span className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider">
          {has ? <ShieldAlert className="h-4 w-4 text-rose-300" aria-hidden /> : <ShieldCheck className="h-4 w-4 text-slate-400" aria-hidden />}
          <span className={has ? "text-rose-300" : "text-slate-400"}>Allergies</span>
        </span>
        {has ? allergies.map((it) => {
          const d = it.data;
          const name = pick(d, "substance", "normalized_substance") || labelOf(d);
          const detail = [pick(d, "reaction") && `reaction: ${pick(d, "reaction")}`, pick(d, "severity") && pick(d, "severity") !== "unknown" ? human(pick(d, "severity")).toLowerCase() : "", statusOf(d.status)?.label.toLowerCase()].filter(Boolean).join(" · ");
          return (
            <span key={it.path} className="inline-flex flex-wrap items-center gap-2">
              <span className="font-display text-[15px] font-semibold first-letter:uppercase text-white">{name}</span>
              {detail && <span className="text-xs text-slate-400">{detail}</span>}
              <Src ctx={ctx} item={it} title={`Allergy: ${name}`} chips={[pick(d, "reaction")].filter(Boolean)} />
            </span>
          );
        }) : <span className="text-sm text-slate-400">None recorded in this conversation</span>}
      </div>
      {questions.length > 0 && (
        <div className="flex flex-1 flex-wrap items-center gap-x-5 gap-y-2 border-t border-white/10 px-5 py-3.5 lg:border-l lg:border-t-0">
          <span className="inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-amber-300"><CircleHelp className="h-4 w-4" aria-hidden />Needs clarification</span>
          {questions.map((it) => {
            const d = it.data;
            const kind = human(pick(d, "type")) || "Open question";
            const detail = pick(d, "description", "details", "value", "name");
            return <span key={it.path} className="text-sm text-amber-100/90"><span className="font-medium">{kind}</span>{detail && detail !== pick(d, "type") && <span className="text-amber-100/60"> — {detail}</span>}</span>;
          })}
        </div>
      )}
    </div>
  );
}

/* ---------- impression: a statement, not a card ---------------------------------------------------------------------------------------- */

export function Impression({ items, ctx }: { items: Item[]; ctx: Ctx }) {
  return (
    <section id="assessment" className="scroll-mt-20">
      {items.map((it, i) => {
        const d = it.data;
        const name = pick(d, "assessment") || labelOf(d);
        const st = statusOf(d.certainty);
        const basis = pick(d, "basis");
        return (
          <motion.div key={it.path} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
            className="relative py-1 pl-6 [&:not(:first-child)]:mt-6">
            <span className="absolute inset-y-0 left-0 w-1 rounded-full bg-gradient-to-b from-cyan-300 via-violet-400 to-transparent" aria-hidden />
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-300">Clinical impression</p>
              {st && <Badge tone={st.tone}>{st.label}</Badge>}
              {reporter(d) && <span className="text-xs text-slate-500">stated by {reporter(d).toLowerCase()}</span>}
            </div>
            <h4 className="mt-2 font-display text-3xl font-semibold leading-tight tracking-tight text-white first-letter:uppercase sm:text-4xl">{name}</h4>
            {basis && <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-300"><span className="text-slate-500">Based on </span>{basis}</p>}
            <div className="mt-3"><Src ctx={ctx} item={it} title={name} chips={[basis].filter(Boolean)} /></div>
          </motion.div>
        );
      })}
    </section>
  );
}

/* ---------- symptoms: one ledger, severity gauge on the left --------------------------------------------------------------------------- */

const SEV: Record<string, { n: number; bar: string; edge: string }> = {
  mild: { n: 1, bar: "bg-emerald-400", edge: "bg-emerald-400" },
  moderate: { n: 2, bar: "bg-amber-400", edge: "bg-amber-400" },
  severe: { n: 3, bar: "bg-rose-400", edge: "bg-rose-400" },
};

export function Symptoms({ items, ctx }: { items: Item[]; ctx: Ctx }) {
  return (
    <section>
      <FlatHeader id="symptoms" icon={Stethoscope} title="Symptoms" count={items.length} tone="rose" />
      <ul className={PANEL}>
        {items.map((it, i) => {
          const d = it.data;
          const name = labelOf(d);
          const sev = SEV[pick(d, "severity").toLowerCase()];
          const meta = [
            pick(d, "duration") && { icon: Clock, text: `For ${pick(d, "duration")}` },
            pick(d, "onset") && { icon: CalendarClock, text: `Began ${pick(d, "onset")}` },
            pick(d, "frequency") && { icon: Repeat, text: pick(d, "frequency") },
            pick(d, "body_site") && { icon: MapPin, text: human(pick(d, "body_site")) },
          ].filter(Boolean) as { icon: LucideIcon; text: string }[];
          const notes = [
            list(d.associated_symptoms).length > 0 && `Also: ${list(d.associated_symptoms).join(", ")}`,
            list(d.aggravating_factors).length > 0 && `Worse with ${list(d.aggravating_factors).join(", ")}`,
            list(d.relieving_factors).length > 0 && `Better with ${list(d.relieving_factors).join(", ")}`,
          ].filter(Boolean) as string[];
          return (
            <motion.li key={it.path} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
              className="relative grid gap-x-5 gap-y-2 border-b border-white/10 px-5 py-4 last:border-b-0 md:grid-cols-[104px_1fr_auto] md:items-center">
              <span className={`absolute inset-y-0 left-0 w-1 ${sev ? sev.edge : "bg-slate-600/60"}`} aria-hidden />
              <div>
                {sev ? (
                  <>
                    <span className="flex gap-1" aria-hidden>{[1, 2, 3].map((n) => <span key={n} className={`h-1.5 w-6 rounded-full ${n <= sev.n ? sev.bar : "bg-white/15"}`} />)}</span>
                    <p className="mt-1 text-[11px] font-medium capitalize text-slate-300">{pick(d, "severity")}</p>
                  </>
                ) : <p className="text-[11px] text-slate-500">Severity not stated</p>}
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <h4 className="font-display text-[15px] font-semibold leading-snug text-white first-letter:uppercase">{name}</h4>
                  <StatusDot raw={d.status} />
                  {pick(d, "category") && <span className="text-[11px] uppercase tracking-wider text-slate-500">{human(pick(d, "category"))}</span>}
                </div>
                {meta.length > 0 && <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">{meta.map((m) => <Meta key={m.text} icon={m.icon}>{m.text}</Meta>)}</div>}
                {notes.map((n) => <p key={n} className="mt-1 text-xs text-slate-400">{n}</p>)}
              </div>
              <div className="flex items-center gap-3 md:flex-col md:items-end md:gap-1.5">
                {by(d) && <span className="text-[11px] text-slate-500">{by(d)}</span>}
                <Src ctx={ctx} item={it} title={name} chips={meta.map((m) => m.text)} />
              </div>
            </motion.li>
          );
        })}
      </ul>
    </section>
  );
}

/* ---------- not present: a checklist ----------------------------------------------------------------------------------------------------- */

export function Denied({ items, ctx }: { items: Item[]; ctx: Ctx }) {
  return (
    <section>
      <FlatHeader id="denied" icon={Ban} title="Reported as not present" count={items.length} tone="mint" />
      <ul className="grid gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((it) => {
          const name = labelOf(it.data);
          const ev = ctx.evidence.get(it.path);
          const n = ev ? ev.segments.filter((s) => s.status === "resolved").length : 0;
          return (
            <li key={it.path}>
              <button type="button" disabled={!ev} onClick={() => ctx.openSource({ item: it, title: `No ${name}`, chips: [by(it.data)].filter(Boolean) })}
                className="group flex w-full items-center gap-3 rounded-xl px-2 py-2.5 text-left transition enabled:hover:bg-white/[0.05] disabled:cursor-default">
                <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-emerald-400/15 text-emerald-300 ring-1 ring-emerald-300/30"><Check className="h-3 w-3" aria-hidden /></span>
                <span className="flex-1 text-sm text-slate-200 first-letter:uppercase">No {name}</span>
                {ev && <span className={`text-[11px] ${n ? "text-cyan-300/80 group-hover:text-cyan-200" : "text-amber-300"}`}>{n ? `${n} source${n === 1 ? "" : "s"}` : "no source"}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/* ---------- history: a record sheet with one lane per kind ------------------------------------------------------------------------------- */

type Lane = { key: string; label: string; icon: LucideIcon; tone: keyof typeof TONE_BOX; items: Item[]; sub: (d: Rec) => string };

export function History({ pmh, surgical, family, social, ctx }: { pmh: Item[]; surgical: Item[]; family: Item[]; social: Item[]; ctx: Ctx }) {
  const lanes: Lane[] = [
    { key: "pmh", label: "Medical history", icon: ClipboardList, tone: "sky", items: pmh, sub: (d) => [pick(d, "duration") && `for ${pick(d, "duration")}`, pick(d, "onset")].filter(Boolean).join(" · ") },
    { key: "surg", label: "Surgical history", icon: Bone, tone: "violet", items: surgical, sub: (d) => pick(d, "timeframe", "date", "when") },
    { key: "fam", label: "Family history", icon: Users, tone: "amber", items: family, sub: (d) => (pick(d, "relation") ? human(pick(d, "relation")) : "") },
    { key: "soc", label: "Social history", icon: Home, tone: "mint", items: social, sub: (d) => {
      const label = labelOf(d).toLowerCase();
      return [pick(d, "category") && human(pick(d, "category")), [pick(d, "details"), pick(d, "description")].find((x) => x && x.toLowerCase() !== label && !label.includes(x.toLowerCase()))].filter(Boolean).join(" · ");
    } },
  ];
  if (!lanes.some((l) => l.items.length)) return null;
  return (
    <section>
      <FlatHeader id="history" icon={ClipboardList} title="History" tone="sky" />
      <div className={PANEL}>
        {lanes.map((l) => {
          const Icon = l.icon;
          return (
            <div key={l.key} className="grid border-b border-white/10 last:border-b-0 md:grid-cols-[210px_1fr]">
              <div className="flex items-center gap-3 bg-white/[0.025] px-5 py-4">
                <span className={`grid h-8 w-8 place-items-center rounded-lg ring-1 ${TONE_BOX[l.tone]}`}><Icon className="h-4 w-4" aria-hidden /></span>
                <div className="leading-tight"><p className="text-sm font-medium text-white">{l.label}</p><p className="text-[11px] text-slate-500">{l.items.length ? `${l.items.length} recorded` : "Not discussed"}</p></div>
              </div>
              <div className="px-5 py-1.5">
                {l.items.length === 0 ? <p className="py-3 text-sm text-slate-600">—</p> : (
                  <ul className="divide-y divide-white/[0.07]">
                    {l.items.map((it) => {
                      const name = labelOf(it.data);
                      const s = l.sub(it.data);
                      return (
                        <li key={it.path} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2.5">
                          <span className="text-sm font-medium text-white first-letter:uppercase">{name}</span>
                          {s && <span className="text-xs text-slate-400">{s}</span>}
                          <StatusDot raw={it.data.status} />
                          <span className="ml-auto"><Src ctx={ctx} item={it} title={name} chips={[s].filter(Boolean)} /></span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* ---------- examination, review of systems, conditions: one sheet ------------------------------------------------------------------------- */

const SUB = "px-5 pb-1 pt-4 text-[11px] font-semibold uppercase tracking-wider text-slate-400";

export function Examination({ exam, ros, conditions, ctx }: { exam: Item[]; ros: Item[]; conditions: Item[]; ctx: Ctx }) {
  const left = exam.length > 0;
  const right = ros.length > 0 || conditions.length > 0;
  if (!left && !right) return null;
  return (
    <section>
      <FlatHeader id="examination" icon={Stethoscope} title="Examination and systems" count={exam.length + ros.length + conditions.length} tone="cyan" />
      <div className={`${PANEL} grid ${left && right ? "lg:grid-cols-2 lg:divide-x lg:divide-white/10" : ""}`}>
        {left && (
          <div>
            <p className={SUB}>Examination findings</p>
            <ul className="divide-y divide-white/[0.07] px-5 pb-2">
              {exam.map((it) => {
                const name = labelOf(it.data);
                const site = pick(it.data, "body_site");
                return (
                  <li key={it.path} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5">
                    {site && <span className="inline-flex items-center gap-1 rounded-md bg-cyan-400/10 px-2 py-0.5 text-[11px] font-medium text-cyan-200 ring-1 ring-cyan-300/25"><MapPin className="h-3 w-3" aria-hidden />{human(site)}</span>}
                    <span className="text-sm text-white first-letter:uppercase">{name}</span>
                    <StatusDot raw={it.data.status} />
                    <span className="ml-auto"><Src ctx={ctx} item={it} title={name} chips={[site].filter(Boolean)} /></span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
        {right && (
          <div>
            {ros.length > 0 && (
              <>
                <p className={SUB}>Review of systems</p>
                <ul className="divide-y divide-white/[0.07] px-5 pb-2">
                  {ros.map((it) => {
                    const name = pick(it.data, "system") || labelOf(it.data);
                    const det = pick(it.data, "details");
                    return (
                      <li key={it.path} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5">
                        <span className="text-sm font-medium text-white first-letter:uppercase">{name}</span>
                        <StatusDot raw={it.data.status} />
                        {det && <span className="text-xs text-slate-400">{det}</span>}
                        <span className="ml-auto"><Src ctx={ctx} item={it} title={name} chips={[det].filter(Boolean)} /></span>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
            {conditions.length > 0 && (
              <>
                <p className={SUB}>Conditions noted</p>
                <ul className="divide-y divide-white/[0.07] px-5 pb-2">
                  {conditions.map((it) => {
                    const name = labelOf(it.data);
                    return (
                      <li key={it.path} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5">
                        <span className="text-sm text-white first-letter:uppercase">{name}</span>
                        <StatusDot raw={it.data.status} />
                        <span className="ml-auto"><Src ctx={ctx} item={it} title={name} chips={[]} /></span>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

/* ---------- medications ------------------------------------------------------------------------------------------------------------- */

export function Medications({ items, ctx }: { items: Item[]; ctx: Ctx }) {
  return (
    <SectionCard id="medications" icon={Pill} title="Medications" count={items.length} tone="violet">
      <div className="-mx-1 overflow-x-auto px-1">
        <table className="w-full min-w-[640px] border-separate border-spacing-y-2 text-left text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-slate-400">
              {["Medicine", "Dose", "Route", "How often", "Status", ""].map((h) => <th key={h} className="px-3 pb-1 font-semibold">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {items.map((it) => {
              const d = it.data;
              const name = labelOf(d);
              const st = statusOf(d.status);
              const note = [pick(d, "generic_name") && pick(d, "generic_name").toLowerCase() !== name.toLowerCase() ? pick(d, "generic_name") : "", pick(d, "indication") && `for ${pick(d, "indication")}`].filter(Boolean).join(" · ");
              const cell = "bg-white/[0.05] px-3 py-3 align-middle first:rounded-l-xl last:rounded-r-xl";
              return (
                <tr key={it.path}>
                  <td className={cell}><p className="font-medium first-letter:uppercase text-white">{name}</p>{note && <p className="text-xs text-slate-400">{note}</p>}</td>
                  <td className={`${cell} text-slate-200`}>{pick(d, "dose") || <span className="text-slate-500">Not stated</span>}</td>
                  <td className={`${cell} first-letter:uppercase text-slate-200`}>{pick(d, "route") || <span className="text-slate-500">–</span>}</td>
                  <td className={`${cell} text-slate-200`}>{pick(d, "frequency") || <span className="text-slate-500">–</span>}</td>
                  <td className={cell}>{st ? <Badge tone={st.tone}>{st.label}</Badge> : <span className="text-slate-500">–</span>}</td>
                  <td className={`${cell} text-right`}><Src ctx={ctx} item={it} title={name} chips={[pick(d, "dose"), pick(d, "frequency")].filter(Boolean)} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

/* ---------- plan ---------------------------------------------------------------------------------------------------------------------- */

type Step = { key: string; icon: LucideIcon; kind: string; title: string; status?: string; meta: string[]; item: Item };

export function Recommendations({ items, total, ctx }: { items: Item[]; total: number; ctx: Ctx }) {
  if (!items.length) return null;
  return (
    <SectionCard id="recommendations" icon={Lightbulb} title="Advice given" count={items.length} tone="cyan">
      <ul className="space-y-2.5">
        {items.map((it) => {
          const title = pick(it.data, "description") || labelOf(it.data);
          return (
            <li key={it.path} className="flex items-start justify-between gap-3">
              <p className="text-[14px] first-letter:uppercase text-slate-100">{title}</p>
              <Src ctx={ctx} item={it} title={title} chips={[]} />
            </li>
          );
        })}
      </ul>
      {total > items.length && <p className="mt-3 text-xs text-slate-400">The first {items.length} of {total} advice items are shown; the rest are in the full record.</p>}
    </SectionCard>
  );
}

export function Plan({ tests, actions, followUp, ctx }: { tests: Item[]; actions: Item[]; followUp: Item[]; ctx: Ctx }) {
  const steps: Step[] = [];
  const seen = new Set<string>();
  const push = (s: Step) => { const k = s.title.toLowerCase().replace(/[^a-z0-9]/g, ""); if (k && !seen.has(k)) { seen.add(k); steps.push(s); } };
  for (const it of tests) {
    const type = pick(it.data, "type").toLowerCase();
    push({ key: it.path, icon: /image|scan|x-?ray|mri|ct/.test(type) ? ScanLine : FlaskConical, kind: type ? human(type) : "Test", title: labelOf(it.data), status: pick(it.data, "status"),
      meta: [pick(it.data, "indication") && `For ${pick(it.data, "indication")}`, pick(it.data, "requested_by") && `Requested by ${human(pick(it.data, "requested_by")).toLowerCase()}`, pick(it.data, "scheduled_datetime")].filter(Boolean) as string[], item: it });
  }
  for (const it of actions) {
    const type = pick(it.data, "action_type");
    push({ key: it.path, icon: /follow/.test(type) ? CalendarClock : ClipboardList, kind: type ? human(type) : "Action", title: pick(it.data, "description") || labelOf(it.data), status: pick(it.data, "status"),
      meta: [pick(it.data, "time_reference"), pick(it.data, "responsible_person") && `Responsible: ${human(pick(it.data, "responsible_person")).toLowerCase()}`].filter(Boolean) as string[], item: it });
  }
  for (const it of followUp) {
    const type = pick(it.data, "type");
    const when = (pick(it.data, "time_reference") || pick(it.data, "normalized_datetime")).toLowerCase();
    // the same visit is often listed both as an action ("return visit, 2 weeks") and as a follow-up: show it once
    if (when && steps.some((x) => /follow|return|review|visit|consult|appointment/.test(`${x.kind} ${x.title}`.toLowerCase()) && x.meta.some((m) => m.toLowerCase() === when))) continue;
    push({ key: it.path, icon: CalendarClock, kind: "Follow-up", title: type ? `Follow-up ${type.toLowerCase()}` : "Follow-up", status: pick(it.data, "status"),
      meta: [pick(it.data, "time_reference"), pick(it.data, "normalized_datetime")].filter(Boolean) as string[], item: it });
  }
  if (!steps.length) return null;
  return (
    <SectionCard id="plan" icon={CalendarClock} title="Plan and next steps" count={steps.length} tone="mint">
      <ol className="relative ml-4 border-l border-white/15 pl-7">
        {steps.map((s, i) => {
          const st = statusOf(s.status);
          const Icon = s.icon;
          return (
            <motion.li key={s.key} initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.06 }} className="relative pb-5 last:pb-0">
              <span className="absolute -left-[46px] top-0 grid h-9 w-9 place-items-center rounded-full bg-[#0b1226] text-emerald-200 ring-2 ring-emerald-300/40"><Icon className="h-4 w-4" aria-hidden /></span>
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-300">{s.kind}</p>
                {st && <Badge tone={st.tone}>{st.label}</Badge>}
              </div>
              <p className="mt-0.5 text-[15px] font-medium first-letter:uppercase text-white">{s.title}</p>
              {s.meta.length > 0 && <div className="mt-1.5 flex flex-wrap gap-1.5">{s.meta.map((m) => <Chip key={m}>{m}</Chip>)}</div>}
              <div className="mt-2"><Src ctx={ctx} item={s.item} title={s.title} chips={s.meta} /></div>
            </motion.li>
          );
        })}
      </ol>
    </SectionCard>
  );
}

