import requests
import yt_dlp
import os
import logging
from shazamio import Shazam
from config import FAST_SAVER_API_KEY
from database import get_channels
from moviepy.editor import VideoFileClip  # Videoni kesish uchun

logger = logging.getLogger(__name__)

def download_social_media_video(url):
    try:
        api_url = f"https://fastsaverapi.com/get-info?token={FAST_SAVER_API_KEY}&url={url}"
        logger.info(f"Sending request to FAST_SAVER_API: {api_url}")
        response = requests.get(api_url)
        logger.info(f"API response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data and not data["error"]:
                download_url = data.get("download_url")
                if download_url:
                    return download_url
            logger.warning(f"No download_url in response: {data}")
            return None
        logger.error(f"API error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Social media download error: {e}")
        return None

def process_youtube_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "downloads/video_%(id)s.%(ext)s",
        "merge_output_format": "mp4",
    }
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting info for YouTube URL: {url}")
            info = ydl.extract_info(url, download=False)
            file_size_mb = info.get("filesize_approx", 0) / (1024 * 1024)
            if file_size_mb < 50:
                ydl.download([url])
                file_path = ydl.prepare_filename(info)
                if os.path.exists(file_path):
                    logger.info(f"Download successful: {file_path}")
                    return file_path
                logger.error(f"File not found: {file_path}")
                return None
            else:
                download_url = info.get("url") or info.get("formats")[-1]["url"]
                logger.info(f"Video too large ({file_size_mb} MB), returning URL: {download_url}")
                return download_url
    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        return None

def download_mp3_from_youtube(query):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/audio_%(id)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Searching YouTube for: {query}")
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
            if not search_results or "entries" not in search_results or not search_results["entries"]:
                logger.error(f"No results found for query: {query}")
                return None
            video_url = search_results["entries"][0]["webpage_url"]
            ydl.download([video_url])
            file_path = f"downloads/audio_{search_results['entries'][0]['id']}.mp3"
            if os.path.exists(file_path):
                logger.info(f"MP3 download successful: {file_path}")
                return file_path
            logger.error(f"MP3 file not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"MP3 download error: {e}")
        return None

async def shazam_video(video_path):
    shazam = Shazam()
    try:
        # Agar video 60 soniyadan uzun bo‘lsa, boshidan 30 soniyani kesib olamiz
        video = VideoFileClip(video_path)
        if video.duration > 60:
            logger.info(f"Video too long ({video.duration} sec), trimming to 30 sec")
            trimmed_path = f"temp_trimmed_{os.path.basename(video_path)}"
            video.subclip(0, 30).write_videofile(trimmed_path, codec="libx264", audio_codec="aac")
            video.close()
            result = await shazam.recognize_song(trimmed_path)
            os.remove(trimmed_path)
        else:
            result = await shazam.recognize_song(video_path)
            video.close()
        
        if result and "track" in result:
            return result["track"]["title"], result["track"]["subtitle"]
        logger.info(f"No track found in video: {video_path}")
        return None, None
    except Exception as e:
        logger.error(f"Shazam video error: {e}")
        return None, None

async def shazam_audio(audio_path):
    shazam = Shazam()
    try:
        result = await shazam.recognize_song(audio_path)
        if result and "track" in result:
            return result["track"]["title"], result["track"]["subtitle"]
        logger.info(f"No track found in audio: {audio_path}")
        return None, None
    except Exception as e:
        logger.error(f"Shazam audio error: {e}")
        return None, None

async def check_membership(bot, user_id):
    channels = get_channels()
    if not channels:
        return True
    try:
        for chat_id, _ in channels:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        logger.error(f"Membership check error for {user_id}: {e}")
        return False