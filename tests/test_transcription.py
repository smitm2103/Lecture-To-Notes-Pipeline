from etl.transcribe import TranscriptionEngine

engine = TranscriptionEngine("base")

result = engine.transcribe("data/raw/lecture.mp4")

print("\n========== TRANSCRIPTION ==========")
print(result["text"])

print("\nLanguage:", result["language"])
print("Segments:", len(result["segments"]))
