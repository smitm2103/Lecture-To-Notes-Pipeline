
from pathlib import Path

from etl.youtube import YouTubeAudioDownloader
from etl.transcribe import TranscriptionEngine
from etl.extract import TranscriptExtractor
from etl.transform import TranscriptTransformer
from etl.validate import TranscriptValidator
from etl.load import TranscriptLoader


def run_youtube_pipeline(video_url):

    print("\n========== LECTUREFLOW YOUTUBE PIPELINE STARTED ==========\n")

    try:
        # Step 1: Download YouTube audio
        print("Step 1: Downloading YouTube audio...")

        downloader = YouTubeAudioDownloader()
        audio_path = downloader.download(video_url)

        print(f"Audio downloaded: {audio_path}\n")

        # Step 2: Transcribe audio
        print("Step 2: Transcribing audio...")

        engine = TranscriptionEngine(model_size="base")
        transcription_result = engine.transcribe(audio_path)

        print("Transcription completed!\n")

        # Step 3: Extract transcript data
        print("Step 3: Extracting transcript data...")

        extractor = TranscriptExtractor()
        extracted_data = extractor.extract(
            transcription_result,
            source_file=audio_path
        )

        print("Extraction completed!\n")

        # Step 4: Transform transcript data
        print("Step 4: Cleaning transcript data...")

        transformer = TranscriptTransformer()
        transformed_data = transformer.transform(extracted_data)

        print("Transformation completed!\n")

        # Step 5: Validate transcript data
        print("Step 5: Validating transcript data...")

        validator = TranscriptValidator()
        validation_result = validator.validate(transformed_data)

        if not validation_result["is_valid"]:
            print("Validation failed:")
            for error in validation_result["errors"]:
                print(f"- {error}")

            return None

        print("Validation successful!\n")

        # Step 6: Save transcript
        print("Step 6: Saving transcript as JSON...")

        loader = TranscriptLoader()
        output_file = loader.load(transformed_data)

        print("\n========== PIPELINE COMPLETED SUCCESSFULLY ==========")
        print(f"Saved file: {output_file}")

        return output_file

    except Exception as error:
        print(f"\nPipeline failed: {error}")
        return None


if __name__ == "__main__":

    youtube_url = input("Enter YouTube lecture URL: ").strip()

    if not youtube_url:
        print("Please enter a valid YouTube URL.")
    else:
        run_youtube_pipeline(youtube_url)
