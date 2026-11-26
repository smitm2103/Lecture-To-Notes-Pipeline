
import json
import re

from notes_generation.generator import LectureNotesGenerator


class QuizGenerator(LectureNotesGenerator):

    def generate(self, transcript, num_questions=10):

        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("Transcript cannot be empty.")

        if not 1 <= num_questions <= 20:
            raise ValueError("Question count must be between 1 and 20.")

        instructions = f"""
You are LectureFlow, an expert academic quiz generator.

Create exactly {num_questions} multiple-choice questions
using ONLY the lecture transcript provided below.

REQUIREMENTS:

1. Each question must test an important lecture concept.
2. Each question must have exactly four options.
3. Each question must have exactly one correct answer.
4. Options must be labelled A, B, C and D.
5. Questions must be clear and student-friendly.
6. Avoid duplicate or repetitive questions.
7. Do not invent facts absent from the transcript.
8. Include a short explanation for every correct answer.
9. Distribute correct answers across A, B, C and D.
10. Do not include questions that cannot be answered
    from the transcript.

RETURN ONLY VALID JSON in this exact structure:

{{
    "title": "Lecture Quiz",
    "questions": [
        {{
            "question": "Question text",
            "options": {{
                "A": "First option",
                "B": "Second option",
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "A",
            "explanation": "Explanation of the correct answer."
        }}
    ]
}}

Do not include Markdown code fences.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                instructions
                + "\n\nLECTURE TRANSCRIPT:\n\n"
                + transcript
            )
        )

        output = (response.text or "").strip()

        if not output:
            raise RuntimeError("Gemini generated an empty quiz.")

        # Remove code fences if Gemini includes them.
        output = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            output,
            flags=re.IGNORECASE
        ).strip()

        try:
            quiz = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Gemini returned invalid quiz JSON: {error}"
            ) from error

        self.validate_quiz(quiz, num_questions)

        return quiz

    @staticmethod
    def validate_quiz(quiz, expected_count):

        if not isinstance(quiz, dict):
            raise ValueError("Quiz must be a JSON object.")

        questions = quiz.get("questions")

        if not isinstance(questions, list):
            raise ValueError("Quiz questions must be a list.")

        if len(questions) != expected_count:
            raise ValueError(
                f"Expected {expected_count} questions, "
                f"but received {len(questions)}."
            )

        required_options = {"A", "B", "C", "D"}

        for index, question in enumerate(questions, start=1):

            if not isinstance(question, dict):
                raise ValueError(
                    f"Question {index} has an invalid format."
                )

            if not question.get("question"):
                raise ValueError(
                    f"Question {index} has no question text."
                )

            options = question.get("options")

            if not isinstance(options, dict):
                raise ValueError(
                    f"Question {index} has invalid options."
                )

            if set(options.keys()) != required_options:
                raise ValueError(
                    f"Question {index} must have options A, B, C and D."
                )

            if any(
                not isinstance(value, str) or not value.strip()
                for value in options.values()
            ):
                raise ValueError(
                    f"Question {index} contains an empty option."
                )

            correct_answer = question.get("correct_answer")

            if correct_answer not in required_options:
                raise ValueError(
                    f"Question {index} has an invalid correct answer."
                )

            if not question.get("explanation"):
                raise ValueError(
                    f"Question {index} has no explanation."
                )

        return True
