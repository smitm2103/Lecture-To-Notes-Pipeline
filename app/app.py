
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
import json
import sys

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_audio_pipeline import run_audio_pipeline
from run_youtube_pipeline import run_youtube_pipeline

from notes_generation.generator import LectureNotesGenerator
from notes_generation.notes_saver import NotesSaver
from notes_generation.quiz_generator import QuizGenerator

from db_config import SessionLocal
from db.models import Lecture, Note, Quiz, QuizAttempt


app = Flask(__name__)

# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / "data" / "raw"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Maximum upload size: 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "mp3", "mp4", "wav", "m4a",
    "webm", "mpeg", "mpga", "ogg"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Save lecture and transcript in MySQL
def save_lecture_to_database(title, file_path, transcript):

    db = SessionLocal()

    try:
        lecture = Lecture(
            title=title,
            file_path=str(file_path),
            transcript=transcript
        )

        db.add(lecture)
        db.commit()
        db.refresh(lecture)

        return lecture.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# Save generated notes separately
def save_notes_to_database(lecture_id, notes):

    db = SessionLocal()

    try:
        note = Note(
            lecture_id=lecture_id,
            content=notes
        )

        db.add(note)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@app.route("/")
def home():
    return render_template("index.html")


# GET ALL LECTURES
@app.route("/api/lectures", methods=["GET"])
def get_lectures():

    db = SessionLocal()

    try:
        lectures = (
            db.query(Lecture)
            .order_by(Lecture.id.desc())
            .all()
        )

        result = []

        for lecture in lectures:

            note = (
                db.query(Note)
                .filter(Note.lecture_id == lecture.id)
                .first()
            )

            result.append({
                "id": lecture.id,
                "title": lecture.title,
                "created_at": (
                    lecture.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if lecture.created_at else None
                ),
                "has_notes": note is not None
            })

        return jsonify({
            "success": True,
            "total_lectures": len(result),
            "total_transcriptions": len(result),
            "lectures": result
        }), 200

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        db.close()


# GET ONE LECTURE'S DETAILS, TRANSCRIPT AND AI NOTES
@app.route("/api/lectures/<int:lecture_id>", methods=["GET"])
def get_lecture_details(lecture_id):

    db = SessionLocal()

    try:
        lecture = (
            db.query(Lecture)
            .filter(Lecture.id == lecture_id)
            .first()
        )

        if lecture is None:
            return jsonify({
                "success": False,
                "message": "Lecture not found."
            }), 404

        note = (
            db.query(Note)
            .filter(Note.lecture_id == lecture_id)
            .order_by(Note.id.desc())
            .first()
        )

        return jsonify({
            "success": True,
            "lecture": {
                "id": lecture.id,
                "title": lecture.title,
                "transcript": lecture.transcript,
                "notes": note.content if note else None,
                "created_at": (
                    lecture.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if lecture.created_at else None
                )
            }
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        db.close()


# UPLOAD AUDIO / VIDEO AND GENERATE NOTES
@app.route("/api/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({
            "success": False,
            "message": "No file received"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "Please select a file"
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Unsupported file format"
        }), 400

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    save_path = UPLOAD_FOLDER / unique_name

    try:
        # Step 1: Save uploaded file
        file.save(save_path)
        print(f"Uploaded file saved: {save_path}")

        # Step 2: Transcribe uploaded file
        transcript_file = run_audio_pipeline(save_path)

        if not transcript_file:
            return jsonify({
                "success": False,
                "message": "Transcription failed."
            }), 500

        # Step 3: Load transcript JSON
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        transcript = transcript_data.get("transcript", "")

        if not transcript or not transcript.strip():
            return jsonify({
                "success": False,
                "message": "Transcript is empty."
            }), 500

        # Step 4: Save lecture and transcript in MySQL
        lecture_id = save_lecture_to_database(
            title=Path(original_name).stem,
            file_path=save_path,
            transcript=transcript
        )

        print(f"Lecture saved in MySQL with ID: {lecture_id}")

        # Step 5: Generate English notes
        generator = LectureNotesGenerator()
        notes = generator.generate(transcript)

        # Step 6: Save Markdown notes
        saver = NotesSaver()

        notes_file = saver.save(
            notes,
            filename=Path(original_name).stem
        )

        # Step 7: Save notes in MySQL
        save_notes_to_database(lecture_id, notes)

        print("Lecture notes saved in MySQL successfully!")

        return jsonify({
            "success": True,
            "message": "Lecture notes generated successfully!",
            "lecture_id": lecture_id,
            "notes": notes,
            "notes_filename": notes_file.name,
            "original_name": original_name
        }), 200

    except Exception as error:
        print(f"Upload processing error: {error}")

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# PROCESS YOUTUBE VIDEO AND GENERATE NOTES
@app.route("/api/youtube", methods=["POST"])
def process_youtube():

    data = request.get_json(silent=True) or {}
    video_url = data.get("url", "").strip()

    if not video_url:
        return jsonify({
            "success": False,
            "message": "Please provide a YouTube URL."
        }), 400

    try:
        # Step 1: Run YouTube transcription pipeline
        transcript_file = run_youtube_pipeline(video_url)

        if not transcript_file:
            return jsonify({
                "success": False,
                "message": "YouTube transcription failed."
            }), 500

        # Step 2: Load transcript JSON
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript_data = json.load(f)

        transcript = transcript_data.get("transcript", "")

        if not transcript or not transcript.strip():
            return jsonify({
                "success": False,
                "message": "YouTube transcript is empty."
            }), 500

        # Step 3: Save lecture and transcript in MySQL
        lecture_id = save_lecture_to_database(
            title=Path(transcript_file).stem,
            file_path=video_url,
            transcript=transcript
        )

        print(f"YouTube lecture saved in MySQL with ID: {lecture_id}")

        # Step 4: Generate English notes
        generator = LectureNotesGenerator()
        notes = generator.generate(transcript)

        # Step 5: Save Markdown notes
        saver = NotesSaver()

        notes_file = saver.save(
            notes,
            filename=Path(transcript_file).stem
        )

        # Step 6: Save notes in MySQL
        save_notes_to_database(lecture_id, notes)

        print("YouTube lecture notes saved in MySQL successfully!")

        return jsonify({
            "success": True,
            "message": "Lecture notes generated successfully!",
            "lecture_id": lecture_id,
            "notes": notes,
            "notes_filename": notes_file.name
        }), 200

    except Exception as error:
        print(f"YouTube processing error: {error}")

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


# GENERATE QUIZ FOR A LECTURE
@app.route("/api/lectures/<int:lecture_id>/quiz", methods=["POST"])
def generate_lecture_quiz(lecture_id):
    db = SessionLocal()

    try:
        lecture = (
            db.query(Lecture)
            .filter(Lecture.id == lecture_id)
            .first()
        )

        if lecture is None:
            return jsonify({
                "success": False,
                "message": "Lecture not found."
            }), 404

        if not lecture.transcript or not lecture.transcript.strip():
            return jsonify({
                "success": False,
                "message": "Lecture transcript is unavailable."
            }), 400

        # Reuse the latest quiz if one already exists.
        existing_quiz = (
            db.query(Quiz)
            .filter(Quiz.lecture_id == lecture_id)
            .order_by(Quiz.id.desc())
            .first()
        )

        if existing_quiz:
            return jsonify({
                "success": True,
                "message": "Quiz already exists.",
                "quiz_id": existing_quiz.id,
                "title": existing_quiz.title,
                "questions": [
                    {
                        "question": question["question"],
                        "options": question["options"]
                    }
                    for question in existing_quiz.questions
                ]
            }), 200

        data = request.get_json(silent=True) or {}
        num_questions = data.get("num_questions", 10)

        if (
            not isinstance(num_questions, int)
            or isinstance(num_questions, bool)
            or not 1 <= num_questions <= 20
        ):
            return jsonify({
                "success": False,
                "message": "Question count must be between 1 and 20."
            }), 400

        # Generate quiz using the lecture transcript.
        generator = QuizGenerator()
        quiz_data = generator.generate(
            lecture.transcript,
            num_questions=num_questions
        )

        quiz = Quiz(
            lecture_id=lecture_id,
            title=quiz_data.get("title", "Lecture Quiz"),
            questions=quiz_data["questions"]
        )

        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return jsonify({
            "success": True,
            "message": "Quiz generated successfully!",
            "quiz_id": quiz.id,
            "title": quiz.title,
            "questions": [
                {
                    "question": question["question"],
                    "options": question["options"]
                }
                for question in quiz.questions
            ]
        }), 201

    except Exception as error:
        db.rollback()
        print(f"Quiz generation error: {error}")

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        db.close()


# GET QUIZ QUESTIONS WITHOUT ANSWER KEY
@app.route("/api/lectures/<int:lecture_id>/quiz", methods=["GET"])
def get_lecture_quiz(lecture_id):

    db = SessionLocal()

    try:
        quiz = (
            db.query(Quiz)
            .filter(Quiz.lecture_id == lecture_id)
            .order_by(Quiz.id.desc())
            .first()
        )

        if quiz is None:
            return jsonify({
                "success": False,
                "message": "No quiz found. Generate a quiz first."
            }), 404

        # Never expose correct answers before submission.
        questions = [
            {
                "question": question["question"],
                "options": question["options"]
            }
            for question in quiz.questions
        ]

        return jsonify({
            "success": True,
            "quiz_id": quiz.id,
            "title": quiz.title,
            "questions": questions
        }), 200

    except Exception as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        db.close()


# SUBMIT QUIZ AND CALCULATE SCORE
@app.route("/api/lectures/<int:lecture_id>/quiz/submit", methods=["POST"])
def submit_lecture_quiz(lecture_id):

    db = SessionLocal()

    try:
        data = request.get_json(silent=True) or {}
        answers = data.get("answers")

        if not isinstance(answers, dict):
            return jsonify({
                "success": False,
                "message": "Answers must be provided as a JSON object."
            }), 400

        quiz = (
            db.query(Quiz)
            .filter(Quiz.lecture_id == lecture_id)
            .order_by(Quiz.id.desc())
            .first()
        )

        if quiz is None:
            return jsonify({
                "success": False,
                "message": "Quiz not found."
            }), 404

        questions = quiz.questions
        total_questions = len(questions)

        # Require an answer for every question.
        expected_keys = {
            str(index)
            for index in range(1, total_questions + 1)
        }

        if set(answers.keys()) != expected_keys:
            return jsonify({
                "success": False,
                "message": "Please answer every question before submitting."
            }), 400

        score = 0
        results = []

        for index, question in enumerate(questions, start=1):

            selected_answer = answers[str(index)]
            correct_answer = question["correct_answer"]

            if selected_answer not in {"A", "B", "C", "D"}:
                return jsonify({
                    "success": False,
                    "message": f"Invalid answer for question {index}."
                }), 400

            is_correct = selected_answer == correct_answer

            if is_correct:
                score += 1

            results.append({
                "question": question["question"],
                "selected_answer": selected_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question["explanation"]
            })

        percentage = round(
            (score / total_questions) * 100,
            2
        )

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            answers=answers,
            score=score,
            total_questions=total_questions,
            percentage=percentage
        )

        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        return jsonify({
            "success": True,
            "message": "Quiz submitted successfully!",
            "attempt_id": attempt.id,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "results": results
        }), 200

    except Exception as error:
        db.rollback()
        print(f"Quiz submission error: {error}")

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    finally:
        db.close()

@app.route(
    "/api/lectures/<int:lecture_id>/quiz/attempts",
    methods=["GET"]
)
def get_quiz_attempts(lecture_id):

    db = SessionLocal()

    try:
        # Check whether the lecture exists.
        lecture = db.query(Lecture).filter(
            Lecture.id == lecture_id
        ).first()

        if not lecture:
            return jsonify({
                "success": False,
                "message": "Lecture not found."
            }), 404

        # Find all quizzes belonging to this lecture.
        quizzes = db.query(Quiz).filter(
            Quiz.lecture_id == lecture_id
        ).all()

        quiz_ids = [quiz.id for quiz in quizzes]

        if not quiz_ids:
            return jsonify({
                "success": True,
                "attempts": [],
                "total_attempts": 0
            }), 200

        # Retrieve attempts, newest first.
        attempts = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id.in_(quiz_ids)
        ).order_by(
            QuizAttempt.created_at.desc()
        ).all()

        attempt_history = []

        for attempt in attempts:
            attempt_history.append({
                "attempt_id": attempt.id,
                "quiz_id": attempt.quiz_id,
                "score": attempt.score,
                "total_questions": attempt.total_questions,
                "percentage": attempt.percentage,
                "created_at": (
                    attempt.created_at.isoformat()
                    if attempt.created_at else None
                )
            })

        return jsonify({
            "success": True,
            "total_attempts": len(attempt_history),
            "attempts": attempt_history
        }), 200

    except Exception as error:
        print(f"Quiz attempt history error: {error}")

        return jsonify({
            "success": False,
            "message": "Unable to retrieve quiz attempts."
        }), 500

    finally:
        db.close()


# FILE SIZE ERROR HANDLER
@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "success": False,
        "message": "File is too large. Maximum size is 500 MB."
    }), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)
