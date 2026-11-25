
from faster_whisper import WhisperModel
from pathlib import Path

class TranscriptionEngine:

    def __init__(self, model_size="base"):
        print("Loading Whisper AI model...")

        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully!")

    def transcribe(self, file_path):

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        segments, info = self.model.transcribe(
            str(file_path),
            beam_size=5,
            vad_filter=True
        )

        results = []
        full_text = []

        for segment in segments:
            text = segment.text.strip()

            results.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text
            })

            full_text.append(text)

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "text": " ".join(full_text),
            "segments": results
        }
