import os
from typing import Any, Dict, List, Optional

import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()

# Global cookie file path
COOKIE_FILE = "tiktok_cookies.txt"


class VideoFormat(BaseModel):
    format_id: str | None = Field(
        default=None, description="Unique identifier for the format"
    )
    resolution: str | None = Field(
        default=None, description="Video resolution or 'audio only'"
    )
    url: str | None = Field(default=None, description="Direct URL to the media")
    has_audio: bool | None = Field(
        default=None, description="Whether the format contains audio"
    )
    has_video: bool | None = Field(
        default=None, description="Whether the format contains video"
    )
    bitrate: float | None = Field(
        default=None, description="Audio bitrate in bits per second"
    )
    audio_codec: str | None = Field(default=None, description="Audio codec used")
    ext: str | None = Field(default=None, description="File extension/container format")
    file_size: int | None = Field(default=None, description="File size in bytes")
    cookies: dict[str, Any] | None = Field(
        default=None, description="Cookies required for download"
    )


class Metadata(BaseModel):
    platform: str = Field(..., description="Source platform of the video")
    title: str = Field(..., description="Title of the video")
    duration: float | None = Field(default=None, description="Duration in seconds")
    thumbnail: str | None = Field(
        default=None, description="URL to the video thumbnail"
    )
    formats: list[VideoFormat] = Field(
        ..., description="Available formats for download"
    )


def get_tiktok_cookies():
    """Fetch TikTok cookies as a guest using Selenium and save in correct format"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        driver.get("https://www.tiktok.com")
        driver.implicitly_wait(10)

        # Get cookies and format them properly
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                f.write(
                    f"{cookie['domain']}\t"
                    f"{'TRUE' if cookie['domain'].startswith('.') else 'FALSE'}\t"
                    f"{cookie['path']}\t"
                    f"{'TRUE' if cookie.get('secure') else 'FALSE'}\t"
                    f"{cookie.get('expiry', '0')}\t"
                    f"{cookie['name']}\t"
                    f"{cookie['value']}\n"
                )
        return True
    except Exception as e:
        print(f"Cookie error: {str(e)}")
        return False
    finally:
        if "driver" in locals():
            driver.quit()


def format_cookies(cookies_str: str | None) -> Dict[str, str] | None:
    """Format cookies from string to dictionary"""
    if not cookies_str:
        return None

    cookies = {}
    parts = cookies_str.split("; ")
    current_name = None

    for part in parts:
        if "=" in part:
            name, value = part.split("=", 1)
            if not name.lower() in ["domain", "path", "secure", "expires"]:
                current_name = name
                cookies[current_name] = value
        elif part.lower() == "secure":
            if current_name:
                cookies[current_name + "_secure"] = True

    return cookies


@app.get("/extract-metadata/", response_model=Metadata)
async def extract_metadata(
    video_url: str = Query(...),
    no_watermark: bool = Query(False),
    refresh_cookies: bool = Query(False),
):
    """
    Extract metadata (e.g., title, duration, formats, streaming URLs) for a video
    from YouTube, Facebook, TikTok, or other supported platforms.

    Includes:
    - MP4 formats (video with or without audio)
    - Audio-only formats (e.g., .m4a files) with detailed audio information (bitrate, codec, format, etc.)
    """
    # Handle cookies
    if refresh_cookies or not os.path.exists(COOKIE_FILE):
        if not get_tiktok_cookies():
            raise HTTPException(500, detail="Cookie generation failed")

    # Define yt-dlp options
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "forceurl": True,  # Only fetch the URL, don't download
    }

    if "tiktok.com" in video_url.lower():
        ydl_opts.update(
            {
                "no_watermark": no_watermark,
                "cookiefile": COOKIE_FILE,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            }
        )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Extract info without downloading
            info = ydl.extract_info(video_url, download=False)

            # Detect platform automatically
            platform = info.get("extractor_key", "Unknown Platform").capitalize()

            # Filter formats to include MP4 video (with or without audio) and audio-only formats
            filtered_formats = [
                {
                    "format_id": fmt.get("format_id"),
                    "resolution": (
                        fmt.get("resolution", "audio only")
                        if fmt.get("vcodec") != "none"
                        else "audio only"
                    ),
                    "url": fmt.get("url"),
                    "has_audio": fmt.get("acodec") != "none",
                    "has_video": fmt.get("vcodec") != "none",
                    "bitrate": fmt.get("abr"),
                    "audio_codec": fmt.get("acodec"),
                    "ext": fmt.get("ext"),
                    "file_size": fmt.get("filesize") or fmt.get("filesize_approx"),
                    "cookies": format_cookies(fmt.get("cookies")),
                }
                for fmt in info.get("formats", [])
                if (
                    (
                        fmt.get("ext") == "mp4" and fmt.get("vcodec") != "none"
                    )  # MP4 video
                    or (
                        fmt.get("acodec") != "none" and fmt.get("vcodec") == "none"
                    )  # Audio
                )
                and not fmt.get("url", "").endswith(".m3u8")  # Exclude .m3u8 playlists
            ]

            # Prepare response data
            metadata = {
                "platform": platform,
                "title": info.get("title", "Unknown Title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "formats": filtered_formats,
            }

            return metadata

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error processing video: {str(e)}"
            )
