
class TranscriptValidator:

    def validate(self, transcript_data):

        errors = []

        if not isinstance(transcript_data, dict):
            raise TypeError("Transcript data must be a dictionary")

        if not transcript_data:
            errors.append("Transcript data is empty")
            return {
                "is_valid": False,
                "errors": errors
            }

        # Validate language
        language = transcript_data.get("language")

        if not language:
            errors.append("Language information is missing")

        # Validate language probability
        probability = transcript_data.get("language_probability")

        if not isinstance(probability, (int, float)):
            errors.append("Invalid language probability")
        elif not 0 <= probability <= 1:
            errors.append("Language probability must be between 0 and 1")

        # Validate transcript
        transcript = transcript_data.get("transcript")

        if not isinstance(transcript, str) or not transcript.strip():
            errors.append("Transcript text is empty or invalid")

        # Validate segments
        segments = transcript_data.get("segments")

        if not isinstance(segments, list):
            errors.append("Segments must be a list")
        else:
            for index, segment in enumerate(segments):

                if not isinstance(segment, dict):
                    errors.append(f"Segment {index} is invalid")
                    continue

                start = segment.get("start")
                end = segment.get("end")
                text = segment.get("text")

                if not isinstance(start, (int, float)):
                    errors.append(f"Segment {index} has invalid start time")
                    continue

                if not isinstance(end, (int, float)):
                    errors.append(f"Segment {index} has invalid end time")
                    continue

                if start < 0 or end < start:
                    errors.append(f"Segment {index} has invalid timestamps")

                if not isinstance(text, str) or not text.strip():
                    errors.append(f"Segment {index} has empty text")

        # Validate segment count
        if isinstance(segments, list):
            if transcript_data.get("total_segments") != len(segments):
                errors.append("Segment count does not match")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
