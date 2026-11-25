
from pathlib import Path
from datetime import datetime


class TranscriptExtractor:

    def extract(self, transcription_result, source_file=None):

        if not isinstance(transcription_result, dict):
            raise TypeError("Transcription result must be a dictionary")

        if not transcription_result:
            raise ValueError("Transcription result is empty")

        language = transcription_result.get("language")
        language_probability = transcription_result.get(
            "language_probability", 0.0
        )
        full_text = transcription_result.get("text", "")
        segments = transcription_result.get("segments", [])

        if not isinstance(full_text, str):
            raise TypeError("Transcript text must be a string")

        if not isinstance(segments, list):
            raise TypeError("Transcript segments must be a list")

        # Extract and organize timestamped segments
        extracted_segments = []

        for segment in segments:

            if not isinstance(segment, dict):
                raise ValueError("Invalid segment format")

            start = float(segment.get("start", 0))
            end = float(segment.get("end", 0))
            text = str(segment.get("text", "")).strip()

            if start < 0 or end < start:
                raise ValueError("Invalid segment timestamps")

            extracted_segments.append({
                "start": start,
                "end": end,
                "text": text
            })

        # Calculate total duration
        duration = 0.0

        if extracted_segments:
            duration = max(
                segment["end"] for segment in extracted_segments
            )

        # Prepare extracted data
        extracted_data = {
            "source_file": (
                Path(source_file).name if source_file else None
            ),
            "language": language,
            "language_probability": language_probability,
            "transcript": full_text.strip(),
            "duration": round(duration, 2),
            "total_segments": len(extracted_segments),
            "segments": extracted_segments,
            "extracted_at": datetime.now().isoformat()
        }

        return extracted_data
