# Single comprehensive call vs decomposed extraction (Qwen3-1.7B) — analysis and recommendation

**DEVELOPMENT-ONLY. Analysis only: no prototype and no inference was run.** Costs below are arithmetic from the measured P00/P01 behaviour (prefill 38 tokens/s, decode 2.76 tokens/s, transcript mean 2,088 tokens) and the tokenizer; they are estimates, not measurements.

## 1. What the evidence says about the cause of partial extraction
- The model is not short of room: completed outputs average 2,450 tokens, about 40% below the cap, yet it extracts one symptom where gold has three and 4 of 168 negatives.
- Many of those omissions come from rules the prompt never stated (conventions, enums, closed lists) rather than from capacity. A decomposed design would also need those rules; splitting does not supply them.
- The part decomposition could help with is attention: each call would carry about half to a fifth of the rules and ask for one kind of fact. That is a hypothesis about a 1.7B model; the data does not test it.

## 2. Candidate architectures
| | A. Single call (P02 draft) | B. Five calls (as proposed) | C. Hybrid, two calls |
|---|---|---|---|
| Calls per record | 1 | 5 | 2 |
| Call 1 | all sections | symptoms + negative findings | history side: chief complaint, symptoms, negative findings, allergies, medical/surgical/family/social history, clinical conditions, review of systems, uncertainties of types allergy_*, duration_disagreement, date_uncertain, conflicting_statement, unknown_speaker |
| Further calls | - | medications + allergies; history; vitals + exam + ROS; assessment + investigations + actions + follow-up | plan side: medications (all statuses), vital signs, physical examination, assessment, investigations, clinical actions, follow-up, uncertainties of types uncertain_dose, medication_discrepancy, adherence_uncertain, incomplete_medication_name |
| Rules per call (tokens) | about 2,760 | about 800-1,200 each | about 1,500 each |

## 3. Runtime and memory (estimated)
Cost model per record: prefill = (rules + transcript + about 30 chat tokens) / 38 s; decode = output tokens x 0.36 s; evidence excluded for B and C in this table (an evidence builder or a separate step is assumed, see section 5).

| | A (compact output, evidence rules) | A (if the model keeps indenting) | B | C |
|---|---:|---:|---:|---:|
| Input tokens per call | about 4,880 | about 4,880 | about 3,000-3,300 x 5 | about 3,600 x 2 |
| Prefill total | 128 s | 128 s | 395-435 s | 190 s |
| Output tokens total | about 1,700-2,100 (compact, with evidence) | about 2,450 | about 1,100-1,400 (compact, no evidence) | about 1,100-1,400 |
| Decode total | 610-760 s | 890 s | 400-500 s | 400-500 s |
| Pipeline loads | 1 | 1 | 1 if the pipeline is reused across calls (changes the per-call load convention) else 5 x 6-42 s | 1-2 |
| **Estimated total** | **about 740-890 s** | about 1,020 s | **about 800-950 s + loads** | **about 590-690 s** |
| Output tokens per call (cap risk) | up to the cap | up to the cap | at most about 600; no truncation expected | about 700-800 |
| Peak memory | same as P01 (about 16.1 GB system used) | same | same model; smaller KV per call | same |

Reading: the dominant cost is decoded tokens and decomposition does not reduce the number of facts to write. Five calls add four extra prefills (about +270-300 s) and gain only what compactness and evidence handling would gain anyway. The hybrid is about the same time as a single call that behaves, and faster than one that does not.

## 4. Quality: potential gains and risks
| Question | Assessment |
|---|---|
| Would focused prompts raise recall? | Plausible for symptoms and negatives (many omissions look like early stopping), unproven. The cheapest honest test is call 1 only of architecture B on the 8 pilot records: about 6 minutes per record (about 3,000 input tokens = 80 s prefill; about 450 output tokens = 160 s), **about 45 minutes in total**, comparing symptoms, negatives, history and allergies against P01 and P02-A. Requires approval. |
| Duplicate extraction across calls | Medications vs clinical_actions (a started drug is both a planned medication and an action in gold): in B this crosses calls. Symptoms vs review of systems vs negatives. Conditions vs past medical history (gold lists the same condition in both: they must be produced together). Rule: sections are disjoint by construction; a section is owned by exactly one call. |
| Contradictions when merging | "No known allergies" (a negative finding) must agree with `allergies = []` and with allergy_uncertain/disputed; these four things must be in the same call (hybrid C does this). Uncertainties reference entities in other sections (`related_entities`): B splits them from their targets. Assigning uncertainty types to the call that owns the entities (C) avoids the problem. A deterministic merge check should reject an output that has both a "No known allergies" negative and a reported allergy without an allergy_disputed type. |
| Speaker attribution | Each call sees the whole transcript and the same speaker instructions; speaker lists and roles are deterministic from the transcript (printed ids and roles) and need not be model output at all. `person_N`-as-role normalisation is a deterministic mapping. |
| Evidence ids | Each call would number its own evidence from EV_001: ids collide. Either the model does not produce evidence (P02-E builder after merging), or renumbering and `supports` path rewriting must be done after merge. Section-disjoint calls keep `supports` paths valid. |
| Validation | Merge = union of disjoint top-level keys; then run the canonical schema validator, the reference rules (evidence symmetric, related_entities resolve) and a check that every call returned all of its sections. A missing call output makes the record incomplete, not "completed". |
| Failure surface | More calls = more places to fail (5 x the chance of a malformed output), but each is short, so truncation risk is lowest. A single failed call loses only its sections, not the record. |
| Same fact twice | Prevented by disjoint ownership; any overlap detected at merge (same category key twice) is a validation error, not silently de-duplicated. |

## 5. Interaction with the evidence problem
Evidence collapse (22/23 and 23/25 outputs) and evidence-driven truncation are independent of how many calls are made. B and C only help if the evidence is produced outside the model (P02-E: deterministic builder from the transcript) or the evidence rules actually work. If they do not, decomposition leaves the largest single failure (grounding 1.8%) unchanged.

## 6. Comparison summary
| Criterion | A. Single call | B. Five calls | C. Two calls |
|---|---|---|---|
| Estimated runtime vs P01 (1,094 s) | about -20% to -32% if compact, -7% if not | about -13% to -27% before pipeline loads; worse if each call loads the pipeline | about -37% to -46% |
| Truncation risk | highest, cut by compactness and evidence rules | lowest | low |
| Likely recall effect | unknown; best-defined rules | possibly best for symptoms/negatives; unproven | possibly useful; unproven |
| Merge risks | none | highest: five section groups and cross references | moderate, manageable by ownership by type |
| New code needed | none beyond the optional runner options | merge, renumber, validate, 5 prompts | merge, validate, 2 prompts |
| Cost of being wrong | one pilot (about 2 h) | 5 prompts to freeze and test | 2 prompts |
| Fits the one-variable principle | yes (prompt text only) | no (changes architecture and several variables) | no |

## 7. Recommendation
1. **Run the single comprehensive prompt first (P02-A, pilot of 8).** Most of the failures are missing definitions and an evidence/format design problem, which are fixed or tested without changing the architecture, and it keeps the comparison with P00 and P01 a pure prompt comparison.
2. **Do not adopt the five-call design.** It adds the most merge and validation risk, does not shorten the dominant decode cost, and is not an effective test of the "focused prompt" idea compared with the cheaper call-1 probe.
3. **Keep the hybrid (C) as the contingent option**, activated only if the pilot shows P02-A still misses symptoms/negatives/history (G5 (a)-(b) fail) while completing records (G1 passes). Its first step is the 45-minute call-1 probe, which needs explicit approval; if the probe shows no recall gain, decomposition is dropped for this model.
4. Independent of this choice, deterministic speaker lists, `confidence`/constant filling and evidence construction belong in a post-processor (P02-E), because they are fixed by the transcript or the schema and cost the model 20-40% of its output.
5. The decision should be taken on measured pilot numbers, not on this document: all runtime figures above are arithmetic estimates and the quality effects of decomposition are untested.
