from db_config import engine
from sqlalchemy import text

with engine.connect() as connection:
    connection.execute(
        text("""
            INSERT INTO lectures
            (title, original_filename, stored_filename, file_path, transcript)
            VALUES
            (:title, :original_filename, :stored_filename, :file_path, :transcript)
        """),
        {
            "title": "Python Test Lecture",
            "original_filename": "test.pdf",
            "stored_filename": "test.pdf",
            "file_path": "data/raw/test.pdf",
            "transcript": "This is a test lecture transcript."
        }
    )

    connection.commit()

print("Lecture inserted successfully!")