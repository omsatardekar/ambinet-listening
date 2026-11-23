import type { Derived, Extraction, Item, Rec, SummaryModel } from "./types";

const isRec = (v: unknown): v is Rec => !!v && typeof v === "object" && !Array.isArray(v);

/** Keys that are bookkeeping, never shown to the reader. */
const HIDDEN = new Set([
  "evidence_ids", "confidence", "role_confidence", "normalized_name", "normalized_value", "normalized_condition", "normalized_procedure",
  "normalized_substance", "normalized_finding", "normalized_assessment", "normalized_datetime", "normalized_date",
]);

export function human(v: unknown): string {
  if (v === null || v === undefined) return "";
  const s = String(v).replace(/_/g, " ").trim();
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

/** Any value as readable text (nested objects such as {value, unit, normalized} included). */
export function text(v: unknown): string {
  if (v === null || v === undefined || v === "") return "";
  if (typeof v === "string") return v.trim();
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return v.map(text).filter(Boolean).join(", ");
  if (isRec(v)) {
    if (typeof v.normalized === "string" && v.normalized.trim()) return v.normalized.trim();
    if (v.value !== undefined && v.value !== null && v.unit !== undefined && v.unit !== null) return `${v.value} ${v.unit}`;
    return Object.entries(v).filter(([k]) => !HIDDEN.has(k)).map(([, x]) => text(x)).filter(Boolean).join(" ");
  }
  return "";
}

export const pick = (d: Rec, ...keys: string[]): string => {
  for (const k of keys) { const t = text(d[k]); if (t) return t; }
  return "";
};

export const list = (v: unknown): string[] => (Array.isArray(v) ? v.map(text).filter(Boolean) : text(v) ? [text(v)] : []);

const LABEL_KEYS = ["value", "name", "finding", "condition", "procedure", "substance", "assessment", "description", "system", "type", "time_reference", "category"];
export const labelOf = (d: Rec): string => pick(d, ...LABEL_KEYS) || "Entry";

export function reporter(d: Rec): string {
  const who = pick(d, "reported_by", "stated_by", "observed_by", "requested_by", "responsible_person");
  return who ? human(who) : "";
}

const meaningful = (d: Rec): boolean => Object.entries(d).some(([k, v]) => !HIDDEN.has(k) && text(v) !== "");

function itemsAt(data: unknown, path: string): Item[] {
  const out: Item[] = [];
  if (Array.isArray(data)) data.forEach((d, i) => { if (isRec(d) && meaningful(d)) out.push({ path: `${path}[${i}]`, data: d }); });
  else if (isRec(data) && meaningful(data)) out.push({ path, data });
  return out;
}

export function buildModel(x: Extraction): SummaryModel {
  const mh = (isRec(x.medical_history) ? x.medical_history : {}) as Rec;
  const at = (key: string) => itemsAt(x[key], key);
  const complaint = itemsAt(x.chief_complaint, "chief_complaint")[0] ?? null;
  return {
    complaint,
    symptoms: at("symptoms"),
    denied: at("negative_findings"),
    pmh: itemsAt(mh.past_medical_history, "medical_history.past_medical_history"),
    surgical: itemsAt(mh.surgical_history, "medical_history.surgical_history"),
    family: itemsAt(mh.family_history, "medical_history.family_history"),
    social: itemsAt(mh.social_history, "medical_history.social_history"),
    meds: at("medications"),
    allergies: at("allergies"),
    vitals: at("vital_signs"),
    exam: at("physical_examination"),
    ros: at("review_of_systems"),
    conditions: at("clinical_conditions"),
    assessment: at("clinical_assessment"),
    tests: at("procedures_and_investigations"),
    actions: at("clinical_actions"),
    followUp: at("follow_up"),
    uncertainties: at("clinical_uncertainties"),
  };
}

export const ROLE_LABEL: Record<string, string> = {
  DOCTOR: "Doctor", PATIENT: "Patient", NURSE: "Nurse", CAREGIVER: "Caregiver", FAMILY_MEMBER: "Family member",
  CLINICAL_STAFF: "Care team", UNKNOWN: "Other speaker",
};

export const clock = (s?: number): string => (typeof s === "number" ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}` : "–");

/** Length of the conversation as far as the linked passages tell us (used to place passages on the visit timeline). */
export function visitSeconds(derived: Derived | null): number {
  let end = 0;
  for (const f of derived?.facts ?? []) for (const s of f.segments) if (typeof s.end_seconds === "number") end = Math.max(end, s.end_seconds);
  return Math.max(end * 1.04, 60);
}

/** Words of an item worth highlighting inside a conversation passage. */
export function highlightTerms(d: Rec): string[] {
  const words = new Set<string>();
  for (const [k, v] of Object.entries(d)) {
    if (HIDDEN.has(k) || ["status", "certainty", "assertion", "temporality", "reported_by", "stated_by", "observed_by", "requested_by", "responsible_person", "category", "type", "action_type"].includes(k)) continue;
    for (const w of text(v).toLowerCase().split(/[^a-z0-9]+/)) if (w.length >= 4) words.add(w);
  }
  return [...words];
}

/** Friendly wording for the statuses the extraction can contain. */
export type Tone = "neutral" | "good" | "warn" | "bad" | "info" | "violet";
export const STATUS: Record<string, { label: string; tone: Tone }> = {
  present: { label: "Present", tone: "bad" }, absent: { label: "Absent", tone: "good" }, resolved: { label: "Resolved", tone: "good" },
  ongoing: { label: "Ongoing", tone: "warn" }, existing: { label: "Known condition", tone: "neutral" }, current: { label: "Current", tone: "warn" },
  currently_used: { label: "Taking", tone: "violet" }, discontinued: { label: "Stopped", tone: "neutral" }, planned: { label: "Planned", tone: "info" },
  completed: { label: "Done", tone: "good" }, done: { label: "Done", tone: "good" }, ordered: { label: "Ordered", tone: "info" },
  conditional: { label: "If needed", tone: "warn" }, provisional: { label: "Provisional", tone: "warn" }, confirmed: { label: "Confirmed", tone: "good" },
  differential: { label: "Possible", tone: "warn" }, uncertain: { label: "Uncertain", tone: "warn" }, reported: { label: "Reported", tone: "info" },
  unknown: { label: "Unknown", tone: "neutral" }, positive: { label: "Positive", tone: "bad" }, negative: { label: "Negative", tone: "good" },
  normal: { label: "Normal", tone: "good" }, abnormal: { label: "Abnormal", tone: "bad" }, unresolved: { label: "Open", tone: "warn" },
  prescribed: { label: "Prescribed", tone: "info" }, started: { label: "Started", tone: "info" }, previously_used: { label: "Used before", tone: "neutral" },
};
export const statusOf = (raw: unknown): { label: string; tone: Tone } | null => {
  const t = text(raw);
  if (!t) return null;
  return STATUS[t.toLowerCase().replace(/ /g, "_")] ?? { label: human(t), tone: "neutral" };
};

/** Warnings from the service, reworded for the person using the screen; technical ones are not shown at all. */
export function friendlyNotes(warnings: string[]): string[] {
  const notes: string[] = [];
  for (const w of warnings) {
    const x = w.toLowerCase();
    if (x.includes("token limit") || x.includes("cut off")) notes.push("The conversation was long, so this summary may be incomplete.");
    else if (x.includes("could not be saved")) notes.push("The summary could not be saved to the patient record. It is shown here only.");
  }
  return [...new Set(notes)];
}

export function friendlyError(code?: string): string {
  switch (code) {
    case "transcript_not_found": case "run_not_ready": return "The conversation is not ready yet. Please finish the transcription first.";
    case "endpoint_auth_failed": case "endpoint_not_configured": case "extraction_environment_missing": return "The summary service is not available right now. Please contact support.";
    case "truncated": return "This conversation was too long to summarise in one go.";
    default: return "We could not prepare the summary this time. Please try again.";
  }
}
