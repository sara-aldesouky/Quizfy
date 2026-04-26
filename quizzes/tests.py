from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quizzes.models import Quiz, StudentFeedback, Submission, StudentProfile, QuizSecurityViolation


class StudentFeedbackViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="student1",
            password="testpass123",
        )
        StudentProfile.objects.create(
            user=self.student,
            first_name="Student",
            second_name="One",
            third_name="Test",
            university_id="2024001",
            city="Riyadh",
            major="CS",
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


class SecureQuizViolationLoggingTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="securestudent",
            password="testpass123",
        )
        StudentProfile.objects.create(
            user=self.student,
            first_name="Secure",
            second_name="Student",
            third_name="User",
            university_id="2024002",
            city="Riyadh",
            major="CS",
        )
        self.teacher = User.objects.create_user(
            username="teachersecure",
            password="testpass123",
            is_staff=True,
        )
        self.quiz = Quiz.objects.create(
            title="Protected Quiz",
            code="SAFE101",
            teacher=self.teacher,
            quiz_type="multiple_choice",
        )
        self.submission = Submission.objects.create(
            quiz=self.quiz,
            student_user=self.student,
            student_name="Secure Student User",
            score=0,
            total=3,
            is_submitted=False,
        )
        self.url = reverse(
            "log_quiz_security_violation",
            kwargs={"quiz_code": self.quiz.code, "submission_id": self.submission.id},
        )

    def test_violation_logging_creates_record(self):
        self.client.force_login(self.student)

        response = self.client.post(
            self.url,
            data='{"violation_type":"TAB_SWITCH","details":"Hidden tab detected."}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuizSecurityViolation.objects.count(), 1)
        violation = QuizSecurityViolation.objects.first()
        self.assertEqual(violation.violation_type, QuizSecurityViolation.TAB_SWITCH)
        self.assertEqual(violation.student, self.student)

    def test_third_violation_requests_auto_submit(self):
        self.client.force_login(self.student)
        for violation_type in [
            QuizSecurityViolation.TAB_SWITCH,
            QuizSecurityViolation.WINDOW_BLUR,
            QuizSecurityViolation.FULLSCREEN_EXIT,
        ]:
            response = self.client.post(
                self.url,
                data=f'{{"violation_type":"{violation_type}","details":"test"}}',
                content_type="application/json",
            )

        payload = response.json()
        self.assertEqual(payload["violation_count"], 3)
        self.assertEqual(payload["security_status"], "High Risk")
        self.assertTrue(payload["should_auto_submit"])
        self.submission.refresh_from_db()
        self.assertTrue(self.submission.is_submitted)
        self.assertIsNotNone(self.submission.submitted_at)
        self.assertIn("result/", payload["result_url"])
