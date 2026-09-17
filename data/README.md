# PRISM data card

PRISM diagnoses LLM hallucinations along four dimensions that correspond to three stages of
generation: memory, instruction, and reasoning. The benchmark contains **9,448 instances** over
**65 sub-tasks**, built from existing benchmarks, enhanced datasets, real-world knowledge, human
exams, and synthetic data (Table 6 of the paper).

| Dimension | Meaning | Sub-tasks | Instances |
|---|---|---:|---:|
| KE — Knowledge Error | the model holds incorrect or outdated knowledge | 15 | 1,933 |
| KM — Knowledge Missing | the model lacks the knowledge the question requires | 22 | 2,078 |
| RE — Reasoning Error | the facts are available but the reasoning fails | 10 | 2,995 |
| IFE — Instruction Following Error | the output violates explicit constraints | 18 | 2,442 |
| **Total** | | **65** | **9,448** |

## Files

Each sub-task is one JSON Lines file under `<dimension>/<sub-category>/<name>.jsonl`, and
`tasks.json` lists every sub-task with its size, prompt, and evaluator.

## Fields

| Field | Present in | Description |
|---|---|---|
| `id` | all | unique item id, `<task id>-<number>` |
| `task` | all | task id, as in `tasks.json` and `prism/tasks.py` |
| `source_id` | all | item id in the original annotation files |
| `question` | all | the question shown to the model, before the task prompt is prepended |
| `answer` | closed-ended tasks | reference answer; `[TRUE]`/`[FALSE]` for the judgement subsets of KM-DSK and `[NO_INFO]` for KM-FK, KM-TK, and KM-NPK, where no answer exists |
| `options` | RE-LF | answer options; the letters A, B, C … are added when the prompt is built |
| `procedure` | RE-PF | intermediate steps appended to the question |
| `test_input`, `test_output` | RE-MRF-Code_Generation | test case shown to the model and its expected output |
| `format` | IFE-EF | requested output format |
| `word_range` | IFE-LC | inclusive `[min, max]` word count |
| `language` | IFE-LgC | required response language |
| `instruction_id`, `kwargs` | IFE-EF-Text_Structure, IFE-CCL | IFEval-style instruction and its arguments |

Open-ended sub-tasks (RE-IIF and RE-MRF-Code_Generation) carry no reference answer: they are scored
by an LLM judge with the prompts in `prompts/judges/`.

## Sub-tasks

| # | Task | Sub-category | Items | Evaluator | Prompt |
|---:|---|---|---:|---|---|
| 1 | `KM-NPK-Private` | Non-Public Knowledge | 288 | `abstain` | `KM-NPK.md` |
| 2 | `KM-DSK-SciQ` | Domain-Specific Knowledge | 254 | `answer_match` | `KM-DSK-Open.md` |
| 3 | `KM-NPK-Organizational` | Non-Public Knowledge | 248 | `abstain` | `KM-NPK.md` |
| 4 | `KM-DSK-PubMedQA` | Domain-Specific Knowledge | 231 | `truth_label` | `KM-DSK.md` |
| 5 | `KM-DSK-Chinese_SafetyQA` | Domain-Specific Knowledge | 188 | `answer_match` | `KM-DSK-Open.md` |
| 6 | `KM-TK-Numeric` | Timely Knowledge | 166 | `abstain` | `KM-TK.md` |
| 7 | `KM-TK-Text` | Timely Knowledge | 109 | `abstain` | `KM-TK.md` |
| 8 | `KM-FK-Biology` | Fictional Knowledge | 98 | `abstain` | `KM-FK.md` |
| 9 | `KM-DSK-RAG-QA-Leaderboard` | Domain-Specific Knowledge | 79 | `truth_label` | `KM-DSK.md` |
| 10 | `KM-DSK-RAG-QA-Leaderboard_Fill` | Domain-Specific Knowledge | 53 | `answer_match` | `KM-DSK-Open.md` |
| 11 | `KM-FK-Literature` | Fictional Knowledge | 53 | `abstain` | `KM-FK.md` |
| 12 | `KM-DSK-StrategyQA` | Domain-Specific Knowledge | 52 | `truth_label` | `KM-DSK.md` |
| 13 | `KM-FK-Awards` | Fictional Knowledge | 34 | `abstain` | `KM-FK.md` |
| 14 | `KM-FK-University` | Fictional Knowledge | 32 | `abstain` | `KM-FK.md` |
| 15 | `KM-FK-Large_Language_Model` | Fictional Knowledge | 29 | `abstain` | `KM-FK.md` |
| 16 | `KM-FK-Competition` | Fictional Knowledge | 28 | `abstain` | `KM-FK.md` |
| 17 | `KM-FK-Festival` | Fictional Knowledge | 26 | `abstain` | `KM-FK.md` |
| 18 | `KM-FK-Country` | Fictional Knowledge | 23 | `abstain` | `KM-FK.md` |
| 19 | `KM-FK-Military` | Fictional Knowledge | 23 | `abstain` | `KM-FK.md` |
| 20 | `KM-FK-Time` | Fictional Knowledge | 22 | `abstain` | `KM-FK.md` |
| 21 | `KM-FK-Phone` | Fictional Knowledge | 21 | `abstain` | `KM-FK.md` |
| 22 | `KM-FK-Dynasty` | Fictional Knowledge | 21 | `abstain` | `KM-FK.md` |
| 23 | `KE-FD-TruthfulQA` | Factual Distortion | 471 | `fact_judge` | `KE-FD.md` |
| 24 | `KE-EIC-WhoQA_Entity` | Entity-Identity Confusion | 241 | `exact` | `KE-EIC-WhoQA_Entity.md` |
| 25 | `KE-EIC-SelfBuilt` | Entity-Identity Confusion | 298 | `judge_equiv` | `KE-EIC-SelfBuilt.md` |
| 26 | `KE-FD-DefAn` | Factual Distortion | 238 | `exact` | `KE-FD.md` |
| 27 | `KE-EIC-WiC` | Entity-Identity Confusion | 196 | `exact` | `KE-EIC-WiC.md` |
| 28 | `KE-IMC-Text` | Intra-Memory Conflict | 95 | `exact` | `KE-IMC.md` |
| 29 | `KE-IMC-Numeric` | Intra-Memory Conflict | 83 | `exact` | `KE-IMC.md` |
| 30 | `KE-FD-Religion` | Factual Distortion | 49 | `fact_judge` | `KE-FD.md` |
| 31 | `KE-FD-Sports` | Factual Distortion | 48 | `fact_judge` | `KE-FD.md` |
| 32 | `KE-FD-ArtCulture` | Factual Distortion | 45 | `fact_judge` | `KE-FD.md` |
| 33 | `KE-FD-LawCrimeMilitary` | Factual Distortion | 40 | `fact_judge` | `KE-FD.md` |
| 34 | `KE-FD-FoodCooking` | Factual Distortion | 38 | `fact_judge` | `KE-FD.md` |
| 35 | `KE-FD-Business` | Factual Distortion | 33 | `fact_judge` | `KE-FD.md` |
| 36 | `KE-FD-Science` | Factual Distortion | 31 | `fact_judge` | `KE-FD.md` |
| 37 | `KE-FD-Language` | Factual Distortion | 27 | `fact_judge` | `KE-FD.md` |
| 38 | `IFE-LC-Approximate` | Length Constraints | 370 | `word_range` | `IFE-LC.md` |
| 39 | `IFE-CCL-Math_Reasoning` | Complex & Cognitive Load | 300 | `ifeval` | `IFE-CCL.md` |
| 40 | `IFE-EF-Data_Schema` | Explicit Format | 251 | `data_format` | `IFE-EF.md` |
| 41 | `IFE-EF-Text_Structure` | Explicit Format | 157 | `ifeval` | `IFE-EF.md` |
| 42 | `IFE-CCL-Length_Format_Mixed` | Complex & Cognitive Load | 143 | `ifeval` | `IFE-CCL.md` |
| 43 | `IFE-LC-Lower_Bound` | Length Constraints | 124 | `word_range` | `IFE-LC.md` |
| 44 | `IFE-LC-Upper_Bound` | Length Constraints | 122 | `word_range` | `IFE-LC.md` |
| 45 | `IFE-CCL-Keyword_Inclusion` | Complex & Cognitive Load | 114 | `ifeval` | `IFE-CCL.md` |
| 46 | `IFE-LgC-Chinese` | Language Constraints | 113 | `language` | `IFE-LgC.md` |
| 47 | `IFE-LgC-German` | Language Constraints | 111 | `language` | `IFE-LgC.md` |
| 48 | `IFE-LgC-French` | Language Constraints | 106 | `language` | `IFE-LgC.md` |
| 49 | `IFE-LgC-Russian` | Language Constraints | 100 | `language` | `IFE-LgC.md` |
| 50 | `IFE-LgC-Japanese` | Language Constraints | 93 | `language` | `IFE-LgC.md` |
| 51 | `IFE-LgC-Spanish` | Language Constraints | 91 | `language` | `IFE-LgC.md` |
| 52 | `IFE-CCL-Start_End_Phrase` | Complex & Cognitive Load | 67 | `ifeval` | `IFE-CCL.md` |
| 53 | `IFE-CCL-No_Comma` | Complex & Cognitive Load | 66 | `ifeval` | `IFE-CCL.md` |
| 54 | `IFE-CCL-Two_Responses` | Complex & Cognitive Load | 65 | `ifeval` | `IFE-CCL.md` |
| 55 | `IFE-CCL-Forbidden_Words` | Complex & Cognitive Load | 49 | `ifeval` | `IFE-CCL.md` |
| 56 | `RE-IIF-Summarize` | Information Integration Failure | 642 | `judge_claims` | `RE-IIF-Summarize.md` |
| 57 | `RE-MRF-Mathematics` | Mathematical Reasoning Failure | 559 | `judge_math` | `RE-MRF-Mathematics.md` |
| 58 | `RE-PF-Subquestion` | Procedural Failure | 333 | `fuzzy` | `RE-PF-Subquestion.md` |
| 59 | `RE-LF-Contextual_Inference` | Logical Fallacy | 286 | `choice` | `RE-LF-Contextual_Inference.md` |
| 60 | `RE-IIF-Simplification` | Information Integration Failure | 257 | `judge_claims` | `RE-IIF-Simplification.md` |
| 61 | `RE-LF-Critical_Reasoning` | Logical Fallacy | 233 | `choice` | `RE-LF-Critical_Reasoning.md` |
| 62 | `RE-MRF-Code_Generation` | Mathematical Reasoning Failure | 233 | `judge_code` | `RE-MRF-Code_Generation.md` |
| 63 | `RE-IIF-Dialogue_Extraction` | Information Integration Failure | 218 | `judge_claims` | `RE-IIF-Dialogue_Extraction.md` |
| 64 | `RE-LF-Cognitive_Traps` | Logical Fallacy | 117 | `choice` | `RE-LF-Cognitive_Traps.md` |
| 65 | `RE-PF-Triplet_Hopping` | Procedural Failure | 117 | `fuzzy` | `RE-PF-Triplet_Hopping.md` |
## Scoring

Every sub-task maps to a percentage score S: `100 x accuracy` for closed-ended tasks, `100 x s / 5`
for the LLM-Eval tasks. Its hallucination rate is `H = 100 - S`, the rate of a dimension is the mean
over its sub-tasks, and the H-Score is the mean of the four dimension rates.

## Notes on this release

- The counts follow Section 2.3 of the paper (9,448 instances; KE 1,933, KM 2,078, RE 2,995, IFE 2,442).
  One duplicated item (identical question and answer) was removed from KE-FD-DefAn, which has 239
  entries in our working files and 238 in the paper.
- The three KE-EIC sub-tasks are named after their content: `WiC` contains word-sense judgements,
  `WhoQA_Entity` contains entity questions with a context passage, and `SelfBuilt` contains the
  self-built category-mismatch questions.
- Reference answers are the ones that come with the original data. The judgement subsets of KM-DSK
  (PubMedQA, RAG-QA-Leaderboard, StrategyQA) use the `[TRUE]`/`[FALSE]` prompt; the open-answer
  subsets (SciQ, Chinese SafetyQA, RAG-QA-Leaderboard_Fill) use the open-answer prompt
  `prompts/tasks/KM-DSK-Open.md` and are scored against their reference answers.
- Responses that are empty or that failed with an API error score 0.

## License

The PRISM annotations are released for non-commercial research use. Sub-tasks derived from public
datasets remain under the licenses of those datasets; please consult the original sources before
redistribution. The code in this repository is under the MIT License.
