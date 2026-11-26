# dataset_v2: fine-tuning data for the Qwen3-0.6B extraction model (short prompt, compact output)

Supersedes `../dataset/` (kept only for reference). Differences: (1) a short 313-token prompt instead of the 2,359-token H1 prompt; (2) the model writes a compact JSON that expands losslessly to the full structure; (3) a proper train / validation / test split in which Batch 1 is NOT trained on (its own README says "evaluation use only"). All data is synthetic; labels are automatically validated, not clinician reviewed.

## Folder contents
| Path | What it is |
|---|---|
| `data/train.jsonl` | 2,856 training examples |
| `data/train_oversampled.jsonl` | the same plus 628 rare or hard examples repeated once (3,484 lines). **Use this one for training**; the repeated cases are listed in `data/oversampled_ids.txt` |
| `data/validation.jsonl` | 250 examples: 190 from training scenarios and 60 from scenarios held out of training (the `split` field says which) |
| `test/test.jsonl` | 973 locked test examples (see SPLIT_PLAN.md). **Never train, tune or select checkpoints on these** |
| `test/TEST_LOCK.json` | the locked id list with the SHA-256 of the list and of the test file |
| `test/raw_inputs/`, `test/raw_labels/` | original transcript and original full label of every test encounter (for scoring) |
| `prompt/short_prompt.txt` | the short prompt template (`{ENCOUNTER_ID}`, `{TRANSCRIPT}`); use it unchanged for training and at inference |
| `codec/compact_codec.py`, `codec/schema_keys.json` | `compact()` and `expand()` for the output; `roundtrip_report.json` shows `expand(compact(label)) == label` for all 4,200 labels |
| `schema/final_label_schema.json` | definition of every label field and allowed value |
| `manifest.csv` | per encounter: batch, split, scenario group, tier, speakers, uncertainties, difficulty, token counts, similarity to train |
| `splits.json`, `coverage_audit.json` | which scenario groups are test or validation, and what each split contains |
| `SPLIT_PLAN.md`, `TRAINING_AND_DEPLOYMENT_PLAN.md` | the reasoning for the split; the training recipe, evaluation and deployment plan |
| `CHECKSUMS.sha256` | SHA-256 of every file |

## Example format (`*.jsonl`, one JSON object per line)
`{"id", "source_batch", "split", "scenario_group", "messages": [{"role": "user", "content": <short prompt + transcript>}, {"role": "assistant", "content": <compact JSON>}]}`
* User message: the short prompt, then one line per segment `[SEG0001] person_1 (DOCTOR): text` (timestamps were removed to save about 690 tokens per example; they carry no clinical information).
* Assistant message: the label with every empty field (`null`, `[]`) left out, `evidence_ids` holding at most two segment ids (`SEG0007`), and `clinical_evidence` omitted. `codec.expand()` restores the complete original structure (all keys, original order, `[]` for `clinical_evidence`, `null` confidence).
* Training uses the Qwen3 chat template with thinking off (the template adds an empty think block to the assistant turn, which is what inference does). Train on assistant tokens only.

## Sizes (Qwen3 tokenizer)
Per example: median 3,115 tokens, **maximum 5,412 (set the maximum sequence length to 5,632 or more)**. One pass over `train.jsonl` is about 9.0 million tokens (30.3 million with the first export); `train_oversampled.jsonl` is about 11.1 million.
