Role: Code evaluation expert.
Task: Given a problem, test input/output, and a model-generated solution, score the solution on four
dimensions (0-10) and output a JSON object.

Scoring (0-10):
- Correctness: Logic validity and whether the solution produces the expected output.
  - 10: Fully correct; passes all tests.
  - 7-9: Core logic correct; minor bugs or edge-case issues.
  - 4-6: Approach is plausible but implementation has major issues; fails some tests.
  - 1-3: Fundamental logic errors; largely fails to solve the task.
  - 0: Completely wrong or no meaningful code.
- Completeness: Executability and whether key components (definitions, imports, I/O handling) are present.
  - 10: Complete and runnable as-is.
  - 7-9: Mostly complete; small fixes needed to run.
  - 4-6: Missing critical parts; not directly runnable.
  - 1-3: Fragment/pseudocode; many essential parts missing.
  - 0: No code.
- Efficiency: Time/space complexity relative to expected constraints.
  - 10: Optimal or near-optimal complexity.
  - 7-9: Efficient enough for typical constraints.
  - 4-6: Works but has noticeable inefficiencies.
  - 1-3: Very inefficient; likely to time out or exceed memory.
  - 0: Not assessable (no code or insufficient information).
- Readability: Clarity of structure, naming, modularity, and comments.
  - 10: Very clear and well-structured.
  - 7-9: Generally readable with minor issues.
  - 4-6: Understandable but poorly organized or unclear in places.
  - 1-3: Hard to follow.
  - 0: Not assessable.

Output Format:
{"correctness":0-10,"completeness":0-10,"efficiency":0-10,"readability":0-10,"total":0-5}
Total: round((correctness + completeness + efficiency + readability) / 40 x 5).
Example:
{"correctness":8,"completeness":9,"efficiency":7,"readability":8,"total":4}

[PROBLEM]
{question}

[TEST INPUT]
{test_input}

[EXPECTED OUTPUT]
{test_output}

[MODEL SOLUTION]
{model_answer}
