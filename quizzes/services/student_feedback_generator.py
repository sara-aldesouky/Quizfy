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
from typing import Dict, List, Any, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


class StudentFeedbackGenerator:
    """Generate AI-powered personalized feedback for student quiz submissions."""
    
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            
            # Extract and parse JSON response
            response_text = response.choices[0].message.content
            logger.debug("Raw API response: %s", response_text[:500])
            
            feedback = json.loads(response_text)
            
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
    
    def _prepare_submission_data(self, submission) -> Dict[str, Any]:
        """
        Extract and analyze submission data for LLM analysis.
        
        Returns: {
            "student_name": str,
            "quiz_code": str,
            "quiz_subject": str,
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
                correct_text = self._get_option_text(question, question.correct_answer)
                
                mistakes.append({
                    "question_number": question.question_number or question.id,
                    "question_text": question.question_text[:200],  # Limit length
                    "correct_option": correct_text,
                    "student_selected": selected_text,
                    "difficulty": question.difficulty or "medium",
                })
        
        return {
            "student_name": submission.student_name,
            "quiz_code": submission.quiz.code,
            "quiz_subject": submission.quiz.subject or "General",
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
- Quiz: {submission_data['quiz_code']} ({submission_data['quiz_subject']})
- Score: {submission_data['score']}/{submission_data['total_questions']} ({submission_data['percentage']:.1f}%)
- Questions with mistakes:
{mistake_details}

TASK:
1. Identify weak topics from the mistakes
2. Detect mistake patterns (concept misunderstanding, careless error, repeated mistakes, misreading)
3. Provide clear, student-friendly explanations
4. Generate flashcards for revision
5. Create practice questions (not duplicates) with solutions
6. Apply DIFFICULTY ADAPTATION:
   - Careless error → increase difficulty by one level
   - Conceptual misunderstanding → keep same difficulty, simplify explanation
   - Repeated mistakes in same topic → keep same/slightly easier difficulty first
   - If already "hard" → keep "hard"

RULES:
- Output ONLY valid JSON (no markdown, no extra text)
- Be specific to the student's mistakes, not generic
- Flashcards must be concise and practical
- Generate 2-3 flashcards per weak topic
- Generate 2-3 practice questions per weak topic
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
      "question": "A new practice question (NOT identical to original)",
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
