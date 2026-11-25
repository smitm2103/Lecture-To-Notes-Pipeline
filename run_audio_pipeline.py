
from pathlib import Path

from etl.transcribe import TranscriptionEngine
from etl.extract import TranscriptExtractor
from etl.transform import TranscriptTransformer
from etl.validate import TranscriptValidator
from etl.load import TranscriptLoader


def run_audio_pipeline(audio_path):

    print("\n========== LECTUREFLOW UPLOAD PIPELINE STARTED ==========\n")

    try:
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Uploaded file not found: {audio_path}"
            )

        # Step 1: Transcribe uploaded audio/video
        print("Step 1: Transcribing uploaded file...")

        engine = TranscriptionEngine(model_size="base")
        transcription_result = engine.transcribe(audio_path)

        print("Transcription completed!\n")

        # Step 2: Extract transcript
        print("Step 2: Extracting transcript data...")

        extractor = TranscriptExtractor()
        extracted_data = extractor.extract(
            transcription_result,
            source_file=audio_path
        )

        print("Extraction completed!\n")

        # Step 3: Transform transcript
        print("Step 3: Cleaning transcript data...")

        transformer = TranscriptTransformer()
        transformed_data = transformer.transform(extracted_data)

        print("Transformation completed!\n")

        # Step 4: Validate transcript
        print("Step 4: Validating transcript...")

        validator = TranscriptValidator()
        validation_result = validator.validate(transformed_data)

        if not validation_result["is_valid"]:
            print("Validation failed:")

            for error in validation_result["errors"]:
                print(f"- {error}")

            return None

        print("Validation successful!\n")

        # Step 5: Save transcript JSON
        print("Step 5: Saving transcript...")

        loader = TranscriptLoader()
        output_file = loader.load(transformed_data)

        print("\n========== UPLOAD PIPELINE COMPLETED ==========")
        print(f"Saved transcript: {output_file}")

        return output_file

    except Exception as error:
        print(f"\nUpload pipeline failed: {error}")
        return None
