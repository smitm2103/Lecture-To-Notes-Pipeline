
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class LectureNotesGenerator:

    def __init__(self, model="gemini-3.8-flash"):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def clean_markdown(self, notes):

        cleaned_lines = []

        for line in notes.splitlines():

            line = line.strip()

            # Fix headings wrapped in bold
            line = re.sub(
                r"^\*\*(#{1,6}\s.*?)\*\*$",
                r"\1",
                line
            )

            # Fix horizontal separators
            if re.fullmatch(r"\*\*---+\*\*", line):
                line = "---"

            # Fix escaped bullet points
            line = re.sub(r"^\\\*\s+", "- ", line)

            # Fix unnecessarily nested bold formatting
            line = re.sub(
                r"\*\*\\\*\\\*(.*?)\\\*\\\*\*",
                r"**\1**",
                line
            )

            # Fix unnecessary LaTeX arrows
            line = line.replace("$\\rightarrow$", "→")

            # Remove unnecessary HTML spacing
            line = line.replace("&#x20;", " ")

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def generate(self, transcript):

        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("Transcript cannot be empty.")

        instructions = """
You are LectureFlow, an expert academic lecture notes generator.

Generate detailed, accurate, professional lecture notes in English.

FORMATTING RULES:

1. Use standard Markdown.
2. Main title must use #.
3. Major sections must use ##.
4. Subsections must use ###.
5. Never bold headings.
6. Use - for bullet points.
7. Use **bold** only for important terms.
8. Never escape Markdown characters unnecessarily.
9. Do not use LaTeX for ordinary text or arrows.
10. Do not add decorative formatting.
11. Return clean Markdown only.

CONTENT RULES:

1. Start with a meaningful lecture title.
2. Include a lecture overview.
3. Explain all major topics and subtopics.
4. Use simple, student-friendly English.
5. Preserve names, dates, prices and important figures.
6. Include examples when supported by the transcript.
7. Identify unclear information separately.
8. Include key takeaways.
9. Include revision questions and answers.
10. Never invent information absent from the transcript.

Return only the finished Markdown notes.
"""

        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                instructions
                + "\n\nLECTURE TRANSCRIPT:\n\n"
                + transcript
            )
        )

        notes = (response.text or "").strip()

        if not notes:
            raise RuntimeError(
                "Gemini generated empty lecture notes."
            )

        # Automatically clean Gemini Markdown output
        notes = self.clean_markdown(notes)

        return notes
