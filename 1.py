import requests
import yt_dlp
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os
load_dotenv()  

API_KEY=os.getenv("FASTSAVER_API_KEY")
BOT_TOKEN=os.getenv("BOT_TOKEN")

def download_youtube_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'video.%(ext)s'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Salom! Instagram yoki YouTube video URL'sini yuboring, men uni yuklab beraman.")

async def get_video(update: Update, context: CallbackContext):
    video_url = update.message.text
    
    if "instagram.com" in video_url:
        url = f"https://fastsaverapi.com/get-info?token={API_KEY}&url={video_url}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if "error" in data and not data["error"]:
                download_url = data['download_url']
                await update.message.reply_video(download_url)
            else:
                await update.message.reply_text("Xatolik: Ma'lumot olishda xato")
        else:
            await update.message.reply_text("API-ga bog‘lanishda xatolik!")
    
    elif "youtube.com" in video_url or "youtu.be" in video_url:
        await update.message.reply_text("Video yuklab olinmoqda, iltimos kuting...")
        video_path = download_youtube_video(video_url)
        with open(video_path, 'rb') as video:
            await update.message.reply_video(video)
    
    else:
        await update.message.reply_text("Noto‘g‘ri URL! Iltimos, Instagram yoki YouTube video URL'sini yuboring.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_video))
    
    application.run_polling()

if __name__ == "__main__":
    main()
