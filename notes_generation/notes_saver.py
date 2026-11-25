
from pathlib import Path
from datetime import datetime


class NotesSaver:

    def __init__(self):
        self.output_dir = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "generated_notes"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, notes, filename="lecture_notes"):

        if not isinstance(notes, str) or not notes.strip():
            raise ValueError("Notes cannot be empty.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_file = self.output_dir / (
            f"{filename}_{timestamp}.md"
        )

        output_file.write_text(
            notes,
            encoding="utf-8"
        )

        print(f"Lecture notes saved successfully: {output_file}")

        return output_file
