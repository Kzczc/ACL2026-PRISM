Role:
You are a strict hallucination auditor.

Task:
Read the original text in [QUESTION] and the model simplification in [MODEL ANSWER]. Identify new or
unsupported factual claims and compute hallucination rate.

OutputFormat:
{ "total_claims": int, "hallucinated_claims": int, "hallucination_rate": float }

Example:
{ "total_claims": 4, "hallucinated_claims": 0, "hallucination_rate": 0.0 }

[QUESTION]
{question}

[MODEL ANSWER]
{model_answer}
