import json
from pathlib import Path
from datetime import datetime


class TranscriptLoader:

    def __init__(self):
        self.output_dir = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "processed"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load(self, transcript_data):

        if not isinstance(transcript_data, dict):
            raise TypeError("Transcript data must be a dictionary")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        source_name = Path(
            transcript_data.get("source_file") or "lecture"
        ).stem

        output_file = self.output_dir / (
            f"{source_name}_{timestamp}.json"
        )

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(
                transcript_data,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(f"Transcript saved successfully: {output_file}")

        return output_file