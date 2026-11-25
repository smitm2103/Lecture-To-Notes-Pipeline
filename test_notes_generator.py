
from notes_generation.generator import LectureNotesGenerator
from notes_generation.notes_saver import NotesSaver

print("Testing LectureFlow Notes Generator...")

generator = LectureNotesGenerator()

sample_transcript = """
HTML stands for HyperText Markup Language.
It is used to create the structure of web pages.
CSS is used to style web pages.
JavaScript adds interactivity to websites.
"""

print("\nGenerating lecture notes...")

notes = generator.generate(sample_transcript)

print("\n========== GENERATED LECTURE NOTES ==========\n")
print(notes)

print("\nSaving lecture notes...")

saver = NotesSaver()
output_file = saver.save(notes, filename="web_development")

print("\n========== TEST COMPLETED ==========")
print(f"Notes file: {output_file}")
