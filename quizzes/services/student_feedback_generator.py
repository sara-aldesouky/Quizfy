"""
StudentFeedbackGenerator - Generates personalized learning feedback for students.

Uses OpenAI to analyze quiz mistakes and generate:
- Weak topics identification
- Mistake pattern analysis
- Revision flashcards
- Adaptive practice questions with solutions
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class StudentFeedbackGenerator:
    """Generate AI-powered personalized feedback for student quiz submissions."""

    FLASHCARD_TARGET = 10
    PRACTICE_TARGET = 7
    PRACTICE_TYPE_SEQUENCE = ["mcq", "true_false", "mcq", "true_false", "mcq", "true_false", "mcq"]

    @classmethod
    def has_expected_feedback_shape(cls, feedback) -> bool:
        flashcards = getattr(feedback, "flashcards", []) or []
        practice_questions = getattr(feedback, "practice_questions", []) or []
        if len(flashcards) != cls.FLASHCARD_TARGET or len(practice_questions) != cls.PRACTICE_TARGET:
            return False
        expected_types = cls.PRACTICE_TYPE_SEQUENCE
        actual_types = [
            str(item.get("type", "")).strip().lower()
            for item in practice_questions
            if isinstance(item, dict)
        ]
        return actual_types == expected_types
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            # Try environment variable
            import os
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not configured. Set in Django settings or environment."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
    
    def generate_feedback(self, submission) -> Dict[str, Any]:
        """
        Generate personalized feedback for a student's quiz submission.
        
        Args:
            submission: Submission instance with answers populated
            
        Returns:
            Dictionary with keys: weak_topics, flashcards, practice_questions
        """
        try:
            # Prepare submission data
            submission_data = self._prepare_submission_data(submission)
            
            # Create LLM prompt
            prompt = self._create_prompt(submission_data, submission)
            
            logger.info(
                "Generating feedback for student=%s quiz=%s submission_id=%d",
                submission.student_name,
                submission.quiz.code,
                submission.id,
            )
            
            # Call OpenAI API
            response = self._create_completion_with_json_fallback(
                {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._system_prompt(),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.7,
                }
            )
            
            # Extract and parse JSON response
            response_text = response.choices[0].message.content or "{}"
            logger.debug("Raw API response: %s", response_text[:500])
            
            feedback = json.loads(self._extract_json_payload(response_text))
            feedback = self._normalize_feedback(feedback, submission_data)
            
            logger.info(
                "Feedback generated: weak_topics=%d flashcards=%d practice_questions=%d",
                len(feedback.get('weak_topics', [])),
                len(feedback.get('flashcards', [])),
                len(feedback.get('practice_questions', [])),
            )
            
            return feedback
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse LLM response as JSON: %s",
                str(e),
                exc_info=True,
            )
            raise ValueError("LLM returned invalid JSON response")
        except Exception as e:
            logger.error(
                "Error generating feedback: %s",
                str(e),
                exc_info=True,
            )
            raise

    def _create_completion_with_json_fallback(self, request_kwargs: Dict[str, Any]):
        try:
            return self.client.chat.completions.create(
                response_format={"type": "json_object"},
                **request_kwargs,
            )
        except Exception as exc:
            if not self._is_unsupported_json_response_format_error(exc):
                raise
            return self.client.chat.completions.create(**request_kwargs)

    def _extract_json_payload(self, content: str) -> str:
        stripped = (content or "").strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped

    def _is_unsupported_json_response_format_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "response_format" in message and "json_object" in message and "not supported" in message
    
    def _prepare_submission_data(self, submission) -> Dict[str, Any]:
        """
        Extract and analyze submission data for LLM analysis.
        
        Returns: {
            "student_name": str,
            "quiz_code": str,
            "quiz_title": str,
            "total_questions": int,
            "score": int,
            "percentage": float,
            "mistakes": [
                {
                    "question_number": int,
                    "question_text": str,
                    "correct_option": str,
                    "student_selected": str,
                    "difficulty": str,
                }
            ]
        }
        """
        mistakes = []
        
        # Iterate through all answers
        for answer in submission.answers.select_related('question').all():
            question = answer.question
            
            if not answer.is_correct:
                # Map option numbers to actual text
                selected_text = self._get_option_text(question, answer.selected)
                correct_text = self._get_option_text(question, question.correct_option)
                
                mistakes.append({
                    "question_number": question.id,
                    "question_text": question.text[:200],  # Limit length
                    "correct_option": correct_text,
                    "student_selected": selected_text,
                    "difficulty": "medium",  # Default difficulty
                })
        
        return {
            "student_name": submission.student_name,
            "quiz_code": submission.quiz.code,
            "quiz_title": submission.quiz.title,
            "total_questions": submission.total,
            "score": submission.score,
            "percentage": (submission.score / submission.total * 100) if submission.total > 0 else 0,
            "mistakes": mistakes,
        }
    
    def _get_option_text(self, question, option_number: Optional[int]) -> str:
        """Get the text of an option by number (1-4)."""
        if not option_number:
            return "Not answered"
        
        option_map = {
            1: "option1",
            2: "option2",
            3: "option3",
            4: "option4",
        }
        
        field_name = option_map.get(option_number, "")
        if field_name:
            return getattr(question, field_name, "") or f"Option {option_number}"
        return f"Option {option_number}"
    
    def _create_prompt(self, submission_data: Dict, submission) -> str:
        """Create the LLM prompt for feedback generation."""
        
        mistake_details = "\n".join([
            f"  Q{m['question_number']}: Student chose '{m['student_selected']}' "
            f"but correct answer is '{m['correct_option']}' (Difficulty: {m['difficulty']})"
            for m in submission_data["mistakes"]
        ])
        
        prompt = f"""Analyze this student's quiz performance and generate personalized learning feedback.

STUDENT PERFORMANCE:
- Name: {submission_data['student_name']}
- Quiz: {submission_data['quiz_code']} - {submission_data['quiz_title']}
- Score: {submission_data['score']}/{submission_data['total_questions']} ({submission_data['percentage']:.1f}%)
- Questions with mistakes:
{mistake_details}

TASK:
1. Identify weak topics from the mistakes
2. Detect mistake patterns (concept misunderstanding, careless error, repeated mistakes, misreading)
3. Provide clear, student-friendly explanations
4. Generate flashcards for revision
5. Create practice questions (not duplicates) with solutions
6. Return EXACTLY 10 flashcards
7. Return EXACTLY 7 practice questions
8. Practice questions must be a mix of:
   - 4 MCQ questions
   - 3 True/False questions
6. Apply DIFFICULTY ADAPTATION:
   - Careless error → increase difficulty by one level
   - Conceptual misunderstanding → keep same difficulty, simplify explanation
   - Repeated mistakes in same topic → keep same/slightly easier difficulty first
   - If already "hard" → keep "hard"

RULES:
- Output ONLY valid JSON (no markdown, no extra text)
- Be specific to the student's mistakes, not generic
- Flashcards must be concise and practical
- Flashcards must total exactly 10 items
- Practice questions must total exactly 7 items
- Every practice question must include a "type" field equal to "mcq" or "true_false"
- MCQ practice questions must include 4 answer options and the correct answer
- True/False practice questions must include the correct answer as either "True" or "False"
- Include step-by-step solutions for each practice question"""
        
        return prompt
    
    def _system_prompt(self) -> str:
        """System prompt for the LLM."""
        return """You are an expert educational assistant that generates personalized learning feedback.

Your output MUST be valid JSON with this exact structure:

{
  "weak_topics": [
    {
      "topic": "Topic name (e.g., 'Photosynthesis')",
      "summary": "Brief 1-2 sentence explanation suitable for the student",
      "mistake_pattern": "Type of mistake: 'concept_misunderstanding', 'careless_error', or 'repeated_mistake'"
    }
  ],
  "flashcards": [
    {
      "topic": "Which weak topic this supports",
      "front": "Question or prompt (one side of flashcard)",
      "back": "Answer or key information",
      "explanation": "Why this matters and how it connects to the student's mistake"
    }
  ],
  "practice_questions": [
    {
      "topic": "Which weak topic this practices",
      "type": "mcq or true_false",
      "question": "A new practice question (NOT identical to original)",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Correct answer text, or True/False",
      "difficulty": "easy", "medium", or "hard",
      "reason_for_difficulty": "Why this difficulty level was chosen based on mistake pattern",
      "solution_steps": "Step-by-step solution or explanation"
    }
  ]
}

CRITICAL RULES:
- Output ONLY the JSON object, nothing else
- All fields must be non-null strings
- Never include the original quiz questions in practice questions
- Match the student's learning level — do not overwhelm
- Be specific to the mistakes shown, not generic explanations"""

    def _normalize_feedback(self, feedback: Dict[str, Any], submission_data: Dict[str, Any]) -> Dict[str, Any]:
        weak_topics = feedback.get("weak_topics", [])
        flashcards = self._normalize_flashcards(feedback.get("flashcards", []), weak_topics, submission_data)
        practice_questions = self._normalize_practice_questions(
            feedback.get("practice_questions", []),
            weak_topics,
            submission_data,
        )
        return {
            "weak_topics": weak_topics,
            "flashcards": flashcards,
            "practice_questions": practice_questions,
        }

    def _normalize_flashcards(
        self,
        raw_flashcards: List[Dict[str, Any]],
        weak_topics: List[Dict[str, Any]],
        submission_data: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        topics = self._topic_names(weak_topics, submission_data)
        mistake_prompts = submission_data.get("mistakes", [])

        for card in raw_flashcards:
            topic = self._safe_text(card.get("topic")) or topics[len(normalized) % len(topics)]
            front = self._safe_text(card.get("front"))
            back = self._safe_text(card.get("back"))
            explanation = self._safe_text(card.get("explanation"))
            if not front or not back:
                continue
            normalized.append(
                {
                    "topic": topic,
                    "front": front,
                    "back": back,
                    "explanation": explanation or f"Review this idea to strengthen {topic}.",
                }
            )
            if len(normalized) == self.FLASHCARD_TARGET:
                return normalized

        index = 0
        while len(normalized) < self.FLASHCARD_TARGET:
            topic = topics[index % len(topics)]
            mistake = mistake_prompts[index % len(mistake_prompts)] if mistake_prompts else {}
            question_number = mistake.get("question_number", index + 1)
            normalized.append(
                {
                    "topic": topic,
                    "front": f"What key idea should you remember from {topic} for question {question_number}?",
                    "back": f"Focus on the core rule behind {topic} and how to avoid the mistake made on question {question_number}.",
                    "explanation": "This saved card was generated to keep your revision set complete.",
                }
            )
            index += 1

        return normalized[: self.FLASHCARD_TARGET]

    def _normalize_practice_questions(
        self,
        raw_questions: List[Dict[str, Any]],
        weak_topics: List[Dict[str, Any]],
        submission_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        topics = self._topic_names(weak_topics, submission_data)
        grouped: Dict[str, List[Dict[str, Any]]] = {"mcq": [], "true_false": []}

        for item in raw_questions:
            normalized = self._normalize_single_practice_question(item, topics)
            grouped[normalized["type"]].append(normalized)

        final_questions: List[Dict[str, Any]] = []
        fallback_index = 0
        for required_type in self.PRACTICE_TYPE_SEQUENCE:
            if grouped[required_type]:
                final_questions.append(grouped[required_type].pop(0))
                continue
            topic = topics[fallback_index % len(topics)]
            final_questions.append(self._build_fallback_practice_question(topic, required_type, fallback_index))
            fallback_index += 1

        return final_questions[: self.PRACTICE_TARGET]

    def _normalize_single_practice_question(
        self,
        item: Dict[str, Any],
        topics: List[str],
    ) -> Dict[str, Any]:
        raw_type = self._safe_text(item.get("type")).lower().replace("/", "_")
        question_type = "true_false" if raw_type in {"true_false", "truefalse", "tf", "t_f"} else "mcq"
        topic = self._safe_text(item.get("topic")) or topics[0]
        question = self._safe_text(item.get("question")) or f"Practice {topic}."
        difficulty = self._safe_text(item.get("difficulty")).lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"
        reason = self._safe_text(item.get("reason_for_difficulty")) or f"This question gives you another chance to practice {topic}."
        solution_steps = self._safe_text(item.get("solution_steps")) or f"Review the main rule for {topic} and solve step by step."

        if question_type == "true_false":
            correct_answer = self._safe_text(item.get("correct_answer"))
            if correct_answer.lower() not in {"true", "false"}:
                correct_answer = "True"
            return {
                "topic": topic,
                "type": "true_false",
                "question": question,
                "options": ["True", "False"],
                "correct_answer": correct_answer.title(),
                "difficulty": difficulty,
                "reason_for_difficulty": reason,
                "solution_steps": solution_steps,
            }

        options = item.get("options")
        if not isinstance(options, list):
            options = []
        cleaned_options = [self._safe_text(option) for option in options if self._safe_text(option)]
        while len(cleaned_options) < 4:
            cleaned_options.append(f"Option {chr(65 + len(cleaned_options))}")
        cleaned_options = cleaned_options[:4]
        correct_answer = self._safe_text(item.get("correct_answer")) or cleaned_options[0]
        if correct_answer not in cleaned_options:
            cleaned_options[0] = correct_answer
        return {
            "topic": topic,
            "type": "mcq",
            "question": question,
            "options": cleaned_options,
            "correct_answer": correct_answer,
            "difficulty": difficulty,
            "reason_for_difficulty": reason,
            "solution_steps": solution_steps,
        }

    def _build_fallback_practice_question(self, topic: str, question_type: str, index: int) -> Dict[str, Any]:
        if question_type == "true_false":
            statement = f"A strong understanding of {topic} helps you choose the correct method before solving."
            return {
                "topic": topic,
                "type": "true_false",
                "question": statement,
                "options": ["True", "False"],
                "correct_answer": "True",
                "difficulty": "medium",
                "reason_for_difficulty": f"This true/false check reinforces a key idea in {topic}.",
                "solution_steps": f"The statement is true because success in {topic} depends on recognizing the correct rule before solving.",
            }

        correct = f"The best answer uses the core rule of {topic} correctly."
        options = [
            correct,
            f"It ignores the main rule of {topic}.",
            f"It applies the wrong method to {topic}.",
            f"It skips an important step in {topic}.",
        ]
        return {
            "topic": topic,
            "type": "mcq",
            "question": f"Which statement best shows the correct thinking for {topic}?",
            "options": options,
            "correct_answer": correct,
            "difficulty": "medium",
            "reason_for_difficulty": f"This MCQ helps you review the main rule behind {topic}.",
            "solution_steps": f"The correct answer is the one that follows the main rule of {topic}. The other options show common mistakes or missing steps.",
        }

    def _topic_names(self, weak_topics: List[Dict[str, Any]], submission_data: Dict[str, Any]) -> List[str]:
        topics = [self._safe_text(topic.get("topic")) for topic in weak_topics if self._safe_text(topic.get("topic"))]
        if topics:
            return topics
        mistakes = submission_data.get("mistakes", [])
        if mistakes:
            return [f"Question {mistakes[0].get('question_number', 1)} Review"]
        return ["General Review"]

    def _safe_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()
