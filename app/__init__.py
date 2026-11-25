
import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request
from sqlalchemy import text
from db_config import engine


# Create the Flask application
app = Flask(__name__)

# Find the root project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folder where uploaded media will be stored
UPLOAD_FOLDER = PROJECT_ROOT / "data" / "raw"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# Maximum upload size: 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {"mp3", "mp4"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/", methods=["GET", "POST"])
def upload_lecture():

    message = None

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        lecture_url = request.form.get("lecture_url", "").strip()
        media = request.files.get("media")

        if not title:
            message = "Please enter a lecture title."

        elif media and media.filename:

            if not allowed_file(media.filename):
                message = "Only MP3 and MP4 files are supported."

            else:
                original_filename = media.filename
                extension = original_filename.rsplit(".", 1)[1].lower()

                # Generate a unique filename
                stored_filename = f"{uuid.uuid4().hex}.{extension}"

                file_path = UPLOAD_FOLDER / stored_filename

                # Save the uploaded file
                media.save(file_path)

                relative_path = f"data/raw/{stored_filename}"

                try:
                    with engine.begin() as connection:
                        connection.execute(
                            text("""
                                INSERT INTO lectures
                                (title, original_filename, stored_filename,
                                 file_path, status)
                                VALUES (:title, :original_filename,
                                        :stored_filename, :file_path,
                                        :status)
                            """),
                            {
                                "title": title,
                                "original_filename": original_filename,
                                "stored_filename": stored_filename,
                                "file_path": relative_path,
                                "status": "uploaded",
                            }
                        )

                    message = "Lecture file uploaded successfully!"

                except Exception as error:
                    if file_path.exists():
                        file_path.unlink()

                    message = f"Database error: {error}"

        elif lecture_url:

            if not lecture_url.startswith(("http://", "https://")):
                message = "Please enter a valid HTTP or HTTPS URL."

            else:
                try:
                    with engine.begin() as connection:
                        connection.execute(
                            text("""
                                INSERT INTO lectures
                                (title, original_filename, stored_filename,
                                 file_path, status)
                                VALUES (:title, :original_filename,
                                        :stored_filename, :file_path,
                                        :status)
                            """),
                            {
                                "title": title,
                                "original_filename": "Online lecture",
                                "stored_filename": "Online lecture link",
                                "file_path": lecture_url,
                                "status": "uploaded",
                            }
                        )

                    message = "Lecture link saved successfully!"

                except Exception as error:
                    message = f"Database error: {error}"

        else:
            message = "Please upload an MP3/MP4 or enter a lecture URL."

    return render_template("upload.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)
