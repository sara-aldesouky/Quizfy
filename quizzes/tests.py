from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quizzes.models import Quiz, StudentFeedback, Submission


class StudentFeedbackViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            password="testpass123",
        )
        self.quiz = Quiz.objects.create(
            title="Biology Review",
            code="BIO101",
            teacher=User.objects.create_user(username="teacher1", password="testpass123", is_staff=True),
            quiz_type="multiple_choice",
        )
        self.submission = Submission.objects.create(
            quiz=self.quiz,
            student_user=self.student,
            student_name="Student One",
            score=3,
            total=5,
            is_submitted=True,
        )
        self.feedback = StudentFeedback.objects.create(
            submission=self.submission,
            weak_topics=[],
            flashcards=[
                {
                    "topic": "Cells",
                    "front": f"Front {index}",
                    "back": f"Back {index}",
                    "explanation": f"Explanation {index}",
                }
                for index in range(10)
            ],
            practice_questions=[
                {
                    "topic": "Cells",
                    "type": "mcq" if index % 2 == 0 else "true_false",
                    "question": f"Practice question {index + 1}",
                    "options": ["Answer A", "Answer B", "Answer C", "Answer D"] if index % 2 == 0 else ["True", "False"],
                    "correct_answer": "Answer A" if index % 2 == 0 else "True",
                    "difficulty": "medium",
                    "reason_for_difficulty": "Review the concept again.",
                    "solution_steps": "Because this matches the core rule.",
                }
                for index in range(7)
            ],
        )
        self.url = reverse(
            "student_feedback",
            kwargs={"quiz_code": self.quiz.code, "submission_id": self.submission.id},
        )

    def test_student_feedback_post_saves_practice_attempts(self):
        self.client.force_login(self.student)

        payload = {
            "practice_answer_0": "Answer A",
            "practice_answer_1": "True",
            "practice_answer_2": "Answer B",
            "practice_answer_3": "False",
            "practice_answer_4": "Answer A",
            "practice_answer_5": "True",
            "practice_answer_6": "Answer D",
        }
        response = self.client.post(self.url, payload)

        self.assertRedirects(response, self.url)
        self.feedback.refresh_from_db()
        self.assertEqual(len(self.feedback.practice_question_attempts), 7)
        self.assertIsNotNone(self.feedback.practice_attempted_at)
        self.assertTrue(self.feedback.practice_question_attempts[0]["is_correct"])
        self.assertFalse(self.feedback.practice_question_attempts[2]["is_correct"])

    def test_student_feedback_get_shows_saved_review_results(self):
        self.client.force_login(self.student)
        self.feedback.practice_question_attempts = [
            {
                "question_index": index,
                "selected_answer": "Answer A" if index % 2 == 0 else "True",
                "correct_answer": "Answer A" if index % 2 == 0 else "True",
                "is_correct": True,
            }
            for index in range(7)
        ]
        self.feedback.save(update_fields=["practice_question_attempts"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saved practice result: 7/7 correct")
        self.assertContains(response, "Correct answer:")
        self.assertContains(response, "These answers stay saved with this quiz attempt.")
