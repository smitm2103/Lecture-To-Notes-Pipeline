
import re


class TranscriptTransformer:

    def transform(self, extracted_data):

        if not isinstance(extracted_data, dict):
            raise TypeError("Extracted data must be a dictionary")

        if not extracted_data:
            raise ValueError("Extracted data is empty")

        transformed_data = extracted_data.copy()

        # Clean complete transcript
        transcript = transformed_data.get("transcript", "")

        if not isinstance(transcript, str):
            raise TypeError("Transcript must be a string")

        transcript = re.sub(r"\s+", " ", transcript).strip()

        transformed_data["transcript"] = transcript

        # Clean timestamped segments
        segments = transformed_data.get("segments", [])

        if not isinstance(segments, list):
            raise TypeError("Segments must be a list")

        cleaned_segments = []

        for segment in segments:

            if not isinstance(segment, dict):
                continue

            text = str(segment.get("text", ""))

            text = re.sub(r"\s+", " ", text).strip()

            if not text:
                continue

            cleaned_segments.append({
                "start": round(float(segment["start"]), 2),
                "end": round(float(segment["end"]), 2),
                "text": text
            })

        transformed_data["segments"] = cleaned_segments

        # Update segment count
        transformed_data["total_segments"] = len(cleaned_segments)

        return transformed_data
