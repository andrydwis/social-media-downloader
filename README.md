# Social Media Downloader

**Social Media Downloader** is a FastAPI-based web service designed to extract and download media content (videos, audio, etc.) from popular social media platforms like TikTok. It provides an easy-to-use API endpoint to fetch media URLs, metadata, and other relevant information.

---

## Features

- **TikTok Video Extraction**: Extract videos with or without watermarks.
- **Cookie Management**: Automatically handles TikTok cookies for guest access.
- **Format Filtering**: Filters and returns only relevant formats (e.g., MP4 videos and audio-only streams).
- **Metadata Retrieval**: Provides metadata such as title, duration, thumbnail URL, and available formats.
- **Customizable Options**: Allows users to specify whether they want the video without a watermark.

---

## Installation

### Prerequisites

1. **Python 3.12 or higher**: Ensure you have Python installed on your system.
2. **Chrome Browser**: Required for Selenium to fetch TikTok cookies.
3. **Chromedriver**: Automatically managed by `webdriver-manager`.

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/social-media-downloader.git
   cd social-media-downloader
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Start the FastAPI server:
   ```bash
   poetry run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. The API will be available at `http://localhost:8000`.

---

## Usage

### API Endpoint

#### `/extract/`

Extracts media information from a given video URL.

**Parameters**:

- `video_url` (required): The URL of the video to extract.
- `no_watermark` (optional, default=False): Set to `True` to attempt downloading the video without a watermark.
- `refresh_cookies` (optional, default=False): Set to `True` to force refresh TikTok cookies.

**Example Request**:

```bash
curl "http://localhost:8000/extract/?video_url=https://www.tiktok.com/@user/video/123456789&no_watermark=True"
```

**Example Response**:

```json
{
  "title": "Funny Cat Video",
  "duration": 15,
  "thumbnail": "https://example.com/thumbnail.jpg",
  "formats": [
    {
      "format_id": "1",
      "resolution": "1080x1920",
      "url": "https://example.com/video.mp4",
      "has_audio": true,
      "has_video": true,
      "bitrate": 128000,
      "audio_codec": "aac",
      "ext": "mp4",
      "file_size": 1234567,
      "cookies": null
    },
    {
      "format_id": "2",
      "resolution": "audio only",
      "url": "https://example.com/audio.m4a",
      "has_audio": true,
      "has_video": false,
      "bitrate": 128000,
      "audio_codec": "opus",
      "ext": "m4a",
      "file_size": 123456,
      "cookies": null
    }
  ]
}
```

---

## Dependencies

- **FastAPI**: For building the API server.
- **yt-dlp**: For extracting media information and downloading content.
- **Selenium**: For automating browser interactions to fetch TikTok cookies.
- **webdriver-manager**: For managing ChromeDriver installations.

---

## Configuration

### Cookie File

The project uses a global cookie file (`tiktok_cookies.txt`) to store TikTok cookies. If the file does not exist or needs to be refreshed, the API will automatically fetch new cookies using Selenium.

---

## Error Handling

- **HTTP 400**: Invalid request parameters or issues during extraction.
- **HTTP 500**: Internal server errors, such as failure to generate cookies.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## Acknowledgments

- Thanks to the developers of `yt-dlp`, `FastAPI`, and `Selenium` for their excellent libraries.
- Special thanks to `webdriver-manager` for simplifying ChromeDriver management.

---

Feel free to reach out if you have any questions or suggestions!