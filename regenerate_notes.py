
import json
from pathlib import Path

from notes_generation.generator import LectureNotesGenerator
from notes_generation.notes_saver import NotesSaver


def main():

    processed_folder = Path("data/processed")

    transcript_files = list(processed_folder.glob("*.json"))

    if not transcript_files:
        print("No transcript JSON files found.")
        return

    # Find the latest transcript
    transcript_file = max(
        transcript_files,
        key=lambda file: file.stat().st_mtime
    )

    print(f"Using transcript: {transcript_file}")

    # Read transcript
    with open(transcript_file, "r", encoding="utf-8") as file:
        transcript_data = json.load(file)

    transcript = transcript_data.get("transcript", "")

    if not transcript.strip():
        print("Transcript is empty.")
        return

    # Generate improved notes
    print("\nGenerating improved lecture notes...")

    generator = LectureNotesGenerator()
    notes = generator.generate(transcript)

    # Save Markdown notes
    saver = NotesSaver()

    notes_file = saver.save(
        notes,
        filename=transcript_file.stem
    )

    print("\nNotes regenerated successfully!")
    print(f"Saved file: {notes_file}")


if __name__ == "__main__":
    main()
