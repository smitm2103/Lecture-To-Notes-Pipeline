
import json
from pathlib import Path

from notes_generation.generator import LectureNotesGenerator
from notes_generation.notes_saver import NotesSaver


def run_notes_pipeline():

    print("\n========== LECTUREFLOW NOTES PIPELINE ==========\n")

    project_dir = Path(__file__).resolve().parent
    transcript_dir = project_dir / "data" / "processed"

    transcript_files = list(transcript_dir.glob("*.json"))

    if not transcript_files:
        print("No processed transcript JSON files found.")
        return

    latest_file = transcript_dir / "Ut4RpySLM6Y_20261126_014157.json"

    print(f"Loading transcript: {latest_file.name}")

    with open(latest_file, "r", encoding="utf-8") as file:
        transcript_data = json.load(file)

    transcript = transcript_data.get("transcript", "")

    if not transcript.strip():
        print("Transcript is empty.")
        return

    print("Transcript loaded successfully!")
    print("\nGenerating English lecture notes...")

    generator = LectureNotesGenerator()
    notes = generator.generate(transcript)

    print("\nSaving generated notes...")

    saver = NotesSaver()
    source_name = Path(
        transcript_data.get("source_file") or "lecture"
    ).stem

    output_file = saver.save(
        notes,
        filename=source_name
    )

    print("\n========== PIPELINE COMPLETED ==========")
    print(f"Generated notes: {output_file}")


if __name__ == "__main__":
    run_notes_pipeline()

