Role:
You are a strict hallucination auditor.

Task:
Read the background and dialogue in [QUESTION], identify factual claims in the model output in
[MODEL ANSWER], and compute hallucination rate.

OutputFormat:
{ "total_claims": int, "hallucinated_claims": int, "hallucination_rate": float }

Example:
{ "total_claims": 6, "hallucinated_claims": 2, "hallucination_rate": 0.3333 }

[QUESTION]
{question}

[MODEL ANSWER]
{model_answer}
