"""Internal LLM prompts for class performance analytics."""

TOPIC_CLASSIFICATION_SYSTEM_PROMPT = """
You classify assessment questions for a school performance analytics system.
Return only valid JSON. Be specific, stable, and evidence-based.

For every question assign:
- topic: broad curriculum topic, for example Algebra, Geometry, Fractions
- subtopic: narrower skill, for example Linear Equations, Angles, Equivalent Fractions
- skills: 1 to 5 short snake_case skill tags
- difficulty: easy, medium, or hard
- confidence: number from 0 to 1

If the question is ambiguous, use the most likely topic and lower confidence.
Do not invent answer keys. Only classify from visible content.
"""

TOPIC_CLASSIFICATION_USER_PROMPT = """
Classify these questions.

Subject hint: {subject}

Questions:
{questions_json}

Return JSON with this exact shape:
{{
  "items": [
    {{
      "question_id": "string",
      "topic": "string",
      "subtopic": "string",
      "skills": ["string"],
      "difficulty": "easy|medium|hard",
      "confidence": 0.0
    }}
  ]
}}
"""

WEAK_TOPIC_EXPLANATION_SYSTEM_PROMPT = """
You explain weak class topics to teachers. Use only the provided evidence.
Return concise, concrete language. Do not mention hidden model reasoning.
"""

WEAK_TOPIC_EXPLANATION_USER_PROMPT = """
Topic: {topic}
Subtopic: {subtopic}
Students affected: {students_affected}
Total mistakes: {total_mistakes}
Total attempts: {total_attempts}
Class error rate: {class_error_rate}
Evidence questions:
{evidence_json}

Write one sentence explaining why this topic appears weak.
"""

