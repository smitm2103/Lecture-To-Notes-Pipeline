
from pathlib import Path
import yt_dlp


class YouTubeAudioDownloader:

    def __init__(self):

        self.output_dir = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "raw"
            / "youtube_downloads"
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(self, video_url):

        if not isinstance(video_url, str) or not video_url.strip():
            raise ValueError("YouTube URL cannot be empty")

        video_url = video_url.strip()

        output_template = str(
            self.output_dir / "%(id)s.%(ext)s"
        )

        options = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": False,
        }

        try:

            print("Extracting YouTube lecture audio...")

            with yt_dlp.YoutubeDL(options) as downloader:

                info = downloader.extract_info(
                    video_url,
                    download=True
                )

                if not info:
                    raise RuntimeError(
                        "Unable to extract video information"
                    )

                requested_downloads = info.get(
                    "requested_downloads", []
                )

                if requested_downloads:
                    downloaded_file = requested_downloads[0].get(
                        "filepath"
                    )
                else:
                    downloaded_file = downloader.prepare_filename(info)

            audio_path = Path(downloaded_file)

            if not audio_path.exists():
                raise FileNotFoundError(
                    "Downloaded audio file was not found"
                )

            print("YouTube audio downloaded successfully!")
            print(f"Saved at: {audio_path}")

            return audio_path

        except Exception as error:

            raise RuntimeError(
                f"YouTube audio extraction failed: {error}"
            ) from error
