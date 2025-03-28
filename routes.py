import os
from typing import Optional

import yt_dlp
from fastapi import FastAPI, HTTPException, Query
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI()

# Global cookie file path
COOKIE_FILE = "tiktok_cookies.txt"


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


@app.get("/extract-metadata/")
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
                    "has_audio": fmt.get("acodec")
                    != "none",  # Indicates whether the format has audio
                    "has_video": fmt.get("vcodec")
                    != "none",  # Indicates whether the format has video
                    "bitrate": fmt.get("abr"),  # Audio bitrate in bits per second
                    "audio_codec": fmt.get("acodec"),  # Audio codec (e.g., opus, aac)
                    "ext": fmt.get("ext"),  # Container format (e.g., mp4, m4a, webm)
                    "file_size": fmt.get("filesize")
                    or fmt.get("filesize_approx"),  # File size in bytes
                    "cookies": fmt.get(
                        "cookies"
                    ),  # Cookies required for downloading the format
                }
                for fmt in info.get("formats", [])
                if (
                    (
                        fmt.get("ext") == "mp4" and fmt.get("vcodec") != "none"
                    )  # MP4 video (with or without audio)
                    or (
                        fmt.get("acodec") != "none" and fmt.get("vcodec") == "none"
                    )  # Audio-only formats
                )
                and not fmt.get("url", "").endswith(".m3u8")  # Exclude .m3u8 playlists
            ]

            # Prepare response data
            metadata = {
                "platform": platform,
                "title": info.get("title", "Unknown Title"),
                "duration": info.get("duration", "Unknown Duration"),
                "thumbnail": info.get("thumbnail", "No Thumbnail"),
                "formats": filtered_formats,
            }

            return metadata

        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error processing video: {str(e)}"
            )
