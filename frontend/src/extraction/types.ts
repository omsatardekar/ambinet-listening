export type Rec = Record<string, unknown>;
export type Item = { path: string; data: Rec };

export type JobStatus = {
  job_id: string;
  status: string;
  stage_message: string;
  warnings: string[];
  error: { code?: string; message?: string } | null;
  started_at: string | null;
  finished_at: string | null;
  saved_to?: { container: string; blob_name: string } | null;
};

export type CitedSegment = {
  segment_id: unknown;
  status: "resolved" | "invalid_format" | "not_found" | "duplicate";
  text?: string;
  speaker_id?: string;
  role?: string;
  start_seconds?: number;
  end_seconds?: number;
  match_score?: number;
};

export type FactEvidence = {
  path: string;
  fact_label: string;
  segments: CitedSegment[];
  source?: "model_cited" | "backend_matched" | "none";
  flags: { kind: string; segment_id?: unknown; count?: number }[];
};

export type Derived = { label: string; notice: string; facts: FactEvidence[]; totals: Record<string, number> };
export type Extraction = Rec;

/** Everything the screen shows, already sorted into the sections a clinician expects. */
export type SummaryModel = {
  complaint: Item | null;
  symptoms: Item[];
  denied: Item[];
  pmh: Item[];
  surgical: Item[];
  family: Item[];
  social: Item[];
  meds: Item[];
  allergies: Item[];
  vitals: Item[];
  exam: Item[];
  ros: Item[];
  conditions: Item[];
  assessment: Item[];
  tests: Item[];
  actions: Item[];
  followUp: Item[];
  uncertainties: Item[];
};

/** What a section card needs to open the source panel. */
export type SourceRequest = { item: Item; title: string; chips: string[] };
export type Ctx = {
  evidence: Map<string, FactEvidence>;
  openSource: (req: SourceRequest) => void;
};
