# Batch 002 generation: working state (read this first after any context reset)
Task: 500 new synthetic encounters 00501-01000 into `../output/inputs|labels` (Batch 001 untouched), hand-authored, validated by the UNMODIFIED Batch 001 validator.
Decisions by user: no sub-agents (cost); same output folders, ids 00501-01000; old git-HEAD Batch 002 (ids 20001+) left deleted.
Workflow: `python3 -B show_plan2.py 0 12 $(cat plan/complex_skip.txt)` lists the next undone plan entries (compact); author `dsl/pNN.txt` (format in `dsl.py` docstring + AUTHOR_GUIDE.md);
`python3 -B dsl.py dsl/pNN.txt` compiles each block -> `drafts/draft_<id>.json` (+ staging) and prints PASS/FAIL. `python3 -B recompile_all.py` rebuilds staging from all drafts.
Lean style: 30-40 turns, ~12 words/turn, tags on turns map to entity keys "k". Lessons (all in AUTHOR_GUIDE.md): finding must be exactly "Allergies" (shortcut "allergy_none"); digits for numbers >12; 'gram' for g; plan cues in planned turns.
Final steps still to do: author remaining ids (check `ls drafts | wc -l`), recompile, copy staging -> ../output (only new ids), dataset_checks.py + audit_batch_002.py, reports, manifest, deviations vs plan.
Complex plan entries are skipped by show_plan2 via plan/complex_skip.txt; write them last (remove from skip list as you go).

## Progress log
- 330/500 (latest); earlier 290/500 drafts pass (ids written by me through dsl/p87.txt). Complex entries (plan kind complex) are being left for last; skipped via plan/complex_skip.txt plus ad-hoc ids (00706,00719,00722,00737,00747,00757,00788,00792,00795,00798,00807,00808,00810,00817 and the ids in complex_skip.txt).
- Known plan deviations to report: speakers added where the plan listed none but a child patient needs a parent (e.g. 00641); features infeasible with listed speakers dropped (00640 duration_disagreement, 00707 date_uncertain); some zero-targets +1 where spoken clinical content had to be labelled.
- Lessons: finding 'Allergies' exact; numbers >12 digits; 'gram'; each planned item needs plan cue words in tagged turn; completed items need did/already/had; ROS needs literal no/nothing/normal/fine; resolved symptom needs gone/settled/went away/resolved; 30 turns minimum.
