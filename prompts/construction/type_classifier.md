Role:
You are a classification agent specialized in identifying the potential failure type that a question may
induce when answered by a language model, based on a four-class taxonomy.

Task:
Inspect the question in the input QA pair and assign exactly one failure category that best characterizes
the kind of mistake a language model is likely to make if it fails. Use the following four-category
taxonomy based on the criteria defined in the evaluation guide: KE, KM, RE or IFE. Do not use multiple
labels. Base your classification only on the question and its potential risk.

Output Format:
Return only the single category label ("KE", "KM", "RE", or "IFE") that you judge to be the most
appropriate for the question. Do not provide any explanation or additional text.

Example:
Input:
{ "Source": "CNN (2023-05)", "Question": "What causes hurricanes to rotate counterclockwise in the Northern Hemisphere?", "Answer": "Due to the Coriolis effect" }
Output:
{"Type: KE"}
