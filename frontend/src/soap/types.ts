export type RosItem = { system: string; finding: string };
export type Medication = { name: string; dose: string; route: string; frequency: string; status: string; comment: string };
export type Problem = { number: number; problem: string; status: string; clinician_impression: string; reasoning: string; icd10_suggestion: { code: string; description: string } | null };
export type PlanItem = { problem_number: number; diagnostics: string[]; treatment: string[]; patient_education: string[]; referrals: string[]; follow_up: string };

export type SoapNote = {
  note_type: string;
  encounter: { encounter_id: string; date_of_service: string; patient_age_sex: string; visit_type: string; participants: string[]; informants: string[] };
  subjective: {
    chief_complaint: string;
    hpi: string;
    hpi_elements: Record<string, string>;
    review_of_systems: { positive: RosItem[]; negative: RosItem[]; not_reviewed: string };
    past_medical_history: string[]; past_surgical_history: string[]; family_history: string[]; social_history: string[];
    medications: Medication[];
    allergies: { status: string; items: { substance: string; reaction: string; comment: string }[]; comment: string };
  };
  objective: {
    vital_signs: { name: string; value: string; unit: string; comment: string }[];
    physical_exam: { system: string; finding: string }[];
    diagnostics: { item: string; result: string; comment: string }[];
    comment: string;
  };
  assessment: { summary: string; problems: Problem[]; differential: string[] };
  plan: { by_problem: PlanItem[]; return_precautions: string[]; follow_up: string; care_coordination: string[] };
  clinician_review: { items_to_verify: { ref: string; topic: string; reason: string }[]; documentation_gaps: string[]; attestation: string };
};

export type SoapReview = { data_quality_flags: { ref: string; issue: string }[]; system_checks: { ref: string; topic: string; reason: string }[] };
export type SoapResult = { note: SoapNote; review: SoapReview; markdown: string };

export type SoapJob = {
  job_id: string;
  status: string;
  stage_message: string;
  warnings: string[];
  error: { code?: string; message?: string } | null;
  started_at: string | null;
  finished_at: string | null;
  saved_to?: { container: string; blob_name: string } | null;
};
