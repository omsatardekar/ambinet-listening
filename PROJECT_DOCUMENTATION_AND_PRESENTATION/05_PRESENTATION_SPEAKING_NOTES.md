# 05 — Presentation speaking notes

Read these out loud once or twice. Change words to what feels natural. Every number here is verified in `01_…` (same 30 records, strict matching, development data only).

---

## A. Two-minute version

"Our project listens to a doctor–patient conversation, turns it into a transcript, and then a small language model has to pull out the medical facts into a fixed JSON form — things like symptoms, medicines, allergies, vital signs and what the doctor advised.

We wanted to do this with a *small* model that runs on a normal laptop, so nothing leaves the machine. We started with Qwen3-0.6B, and later moved to Qwen3-1.7B. We run them with OpenVINO on the laptop's integrated Intel graphics.

We did not train any model. We only changed the instructions, in steps. First, a basic prompt with the JSON form and a few rules. Then we added structure rules. Then, for the 1.7B model, a much more detailed prompt with rules for each section and some invented examples.

We measure it by comparing the model's facts with the expected facts, using precision, recall and F1. On the same 30 test conversations, F1 went from about 0.16 with the basic prompt, to 0.20, to 0.26 with our latest prompt. Medicine and vital signs improved a lot. But the scores are still low — we still miss about four out of five expected facts, and the model almost never finds negative findings or the doctor's instructions.

These results are on development data, with generated labels, so we are not claiming clinical accuracy. Our next step is to fine-tune Qwen3-1.7B with LoRA, which trains a small add-on instead of the whole model. That work has not started yet."

---

## B. Detailed version (about 5–7 minutes)

**1. The problem (≈45 s).** "During a consultation a lot of information is said out loud. A clinician then types it up. We want software to listen and produce a structured note: chief complaint, symptoms, negatives like 'no fever', history, medicines with doses, allergies, vitals, examination, assessment, tests, actions and follow-up. That is called clinical information extraction. Our output is one JSON object with 20 top-level fields."

**2. Why small models (≈30 s).** "Our product design has a small-model stage, and a local model means the conversation does not need to be sent to an outside service. The cost is quality, which our results show. I should say that we didn't write down a formal model-selection study; we started with the smallest Qwen3 so it would run locally."

**3. Why 0.6B first, then 1.7B (≈45 s).** "Qwen3-0.6B was the smallest to try. On a CPU it was slow — about 10 minutes a record — so we converted it with OpenVINO to run on the integrated GPU, which was about 3.7 times faster with the same answers. With the basic prompt it scored an F1 of about 0.05, and the prompt experiments on 0.6B did not get far. So we tried Qwen3-1.7B, the next size up, with the same basic prompt, and it scored about three times higher — 0.16 versus 0.04 on the same 30 records. The price: about seven times slower, much more memory, and many answers cut off because they hit our token limit."

**4. What 'direct inference' means (≈30 s).** "Direct inference means we just give the model the JSON form, a short list of rules and the transcript, and ask for the JSON. No training, no examples. It is our baseline — we call it P00."

**5. How P00, P01, P02 evolved (≈75 s).**
"P00 is the baseline. In P01 we added structure rules — arrays must be arrays, roles must be lower-case words like 'doctor', use only allowed values. It finished more records, but most of the score gain was just that, not better extraction; the model still wrote 'person_1' where a role belongs.
P02 is a more complete prompt. It explains how to decide if a symptom is current or past, has rules for each section — for example blood pressure must be one value like 167/90, and a doctor's question is not a finding — and gives 14 short invented examples. We also stopped asking the model to write evidence records; it only lists segment numbers, and our backend builds the evidence."

**6. What the results show (≈60 s).**
"On the same 30 conversations: P00 gave F1 0.161, P01 0.201, P02 0.258. Precision went from 0.26 to 0.32 and recall from 0.12 to 0.21. Vital signs improved from 0.46 to 0.80 F1 and social history from 0.22 to 0.42. P02 wrote the right speaker role much more consistently. P02 also finished more answers: 28 of 30 compared to 25 for P01.
The bad news: negative findings got worse — one correct out of 51 — clinical actions got zero correct, and physical exam, review of systems and clinical conditions are still zero. Roughly 79% of expected facts are still missed."

**7. Limitations (≈45 s).**
"First, the labels are generated and not checked by clinicians, and we used the same development records to design the prompts, so it's not independent validation. Second, the vital-sign names and social-history categories in our prompt come from the development labels, so some of that gain is matching terminology. Third, it was one run with greedy decoding — no repeats. Fourth, our matching is strict, so a correct paraphrase counts as wrong, and that hurts the free-text categories like actions. Fifth, a run takes about 9 hours on this laptop."

**8. Why fine-tuning (≈30 s).** "Prompts have mostly done what they can: they fix formatting and naming, but not the hard parts like finding denials and instructions. Fine-tuning teaches the model our data's conventions directly. It may also let us shorten the prompt, which saves time."

**9. How LoRA will be used (≈45 s).** "Instead of updating all 1.7 billion parameters, LoRA freezes the model and trains small extra matrices — a small add-on of a few tens of megabytes. It needs much less memory than full fine-tuning. We'd train it on pairs of transcript and correct JSON, validate on separate data, and finally test on conversations the model has never seen. Training on this laptop probably isn't realistic, so we'll plan a cloud GPU, and then convert the merged model back to OpenVINO — that part still needs to be tested."

**10. What we expect (≈20 s).** "We hope for higher recall in the weak categories, fewer cut-off answers and cleaner JSON. We won't know until we test, and we will compare it to P00, P01 and P02 on the same held-out data."

---

## C. Important numbers to remember

| Fact | Number |
|---|---|
| Models | Qwen3-0.6B (≈0.60 B params), Qwen3-1.7B (≈1.72 B params) |
| Hardware | i7-8665U, 15.8 GB RAM, Intel UHD 620 iGPU |
| Dataset | 500 synthetic encounters (Batch 001); 400 locked test never used; 50 dev ids used for prompts |
| Compared set | 30 records, ids 00035…00266 |
| 1.7B F1: P00 / P01 / P02 | 0.161 / 0.201 / 0.258 |
| P02 P / R | 0.323 / 0.214 |
| P02 TP / FP / FN | 234 / 490 / 859 |
| Parsed records P00 / P01 / P02 | 23 / 25 / 28 of 30 |
| 0.6B vs 1.7B direct, same 30 | F1 0.044 vs 0.161 |
| Runtime | P01 9.12 h, P02 9.25 h (30 records) |
| Token cap | 4,096 for 1.7B (0.6B: 6,144) |
| Vital signs F1 P01 → P02 | 0.464 → 0.798 |
| Negative findings P02 | 1 correct of 51 predicted; gold 168 |
| Evidence | 1,240 ids, 98.6% exist; 123 facts without ids |
| Missed gold facts in P02 | ≈79% (859/1,093) |
| Fine-tuning | **Not started** |

---

## D. Likely follow-up questions and suggested answers

1. **Is this accuracy?** "No. It's F1, which balances precision and recall on facts. Accuracy doesn't fit because there are no 'negative' cases to count and each record has different numbers of facts."
2. **Why are the scores so low?** "Strict matching, a hard 18-category schema with many free-text items, a small model, and a prompt-only approach. Even a correct paraphrase counts as wrong. In P01, 352 of the 431 strict false positives were still supported by the transcript — extra or worded differently — so precision is understated. I haven't recomputed that for P02."
3. **Could you just use a bigger model?** "Probably it would score higher; we haven't tested one in this study. This work asks how far a small local model can go."
4. **Why Qwen?** "It has small sizes with a chat format and can be converted to OpenVINO. We did not run a comparison across model families."
5. **Why OpenVINO?** "It lets us use the laptop's integrated GPU, about 3.7× faster than CPU in our test."
6. **Does OpenVINO improve accuracy?** "No, it only runs the model. Conversion keeps the behaviour; it's about speed."
7. **Why did 1.7B fail on some records?** "The answer is longer than our 4,096-token limit and is cut off, so the JSON is incomplete. P02 had two such failures."
8. **Is your prompt overfitted?** "Possibly for naming conventions, because they came from development labels. We checked the examples aren't copies of dev transcripts. A fresh data set is needed."
9. **Are the results reliable?** "They're one deterministic run on 30 records; good for direction, not for tight claims."
10. **Is the data real?** "No — synthetic encounters with generator-produced labels, not verified by clinicians."
11. **What will fine-tuning change?** "It teaches conventions and structure directly. We expect better formatting and some categories to improve; it's not guaranteed."
12. **Can it run on the laptop after fine-tuning?** "We expect so — merge the adapter and convert like before — but we haven't verified it."
13. **How do you prevent leaking test data?** "We keep a sealed locked test set, record every file the run opens, and freeze files by hash."
14. **What if the examiner asks about patient privacy?** "Everything runs locally and the data is synthetic; for real data we'd need proper governance." (Do not claim compliance.)

---

## What I must remember tomorrow
- Say "F1", never "accuracy".
- Say "development data, generated labels, one run".
- Say "fine-tuning is next — not done".
- Lead with the progress: 0.161 → 0.201 → 0.258, and be upfront about the weak categories.
