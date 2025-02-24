import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from dotenv import load_dotenv
import os 
load_dotenv()  

API_KEY=os.getenv("FASTSAVER_API_KEY")
BOT_TOKEN=os.getenv("BOT_TOKEN")
def download_youtube_video(url, format_type, quality):
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best' if format_type == 'video' else 'bestaudio/best',
        'outtmpl': f'video.%(ext)s' if format_type == 'video' else 'audio.%(ext)s'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Salom! Instagram yoki YouTube video URL'sini yuboring, men uni yuklab beraman.")

async def get_video(update: Update, context: CallbackContext):
    video_url = update.message.text
    context.user_data['video_url'] = video_url
    
    keyboard = [
        [InlineKeyboardButton("📸 Instagram", callback_data='instagram')],
        [InlineKeyboardButton("▶️ YouTube", callback_data='youtube')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Qaysi platformadan yuklab olmoqchisiz?", reply_markup=reply_markup)

async def platform_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    video_url = context.user_data.get('video_url')
    
    if query.data == 'instagram':
        url = f"https://fastsaverapi.com/get-info?token={API_KEY}&url={video_url}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data and not data["error"]:
                download_url = data['download_url']
                await query.message.reply_video(download_url)
            else:
                await query.message.reply_text("Xatolik: Ma'lumot olishda xato")
        else:
            await query.message.reply_text("API-ga bog'lanishda xatolik!")
    
    elif query.data == 'youtube':
        keyboard = [
            [InlineKeyboardButton("🎥 Video", callback_data='video')],
            [InlineKeyboardButton("🎵 Audio", callback_data='audio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Qaysi formatda yuklab olishni xohlaysiz?", reply_markup=reply_markup)

async def format_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    format_type = query.data
    context.user_data['format_type'] = format_type
    
    if format_type == 'video':
        keyboard = [
            [InlineKeyboardButton("144p", callback_data='144'),
             InlineKeyboardButton("360p", callback_data='360')],
            [InlineKeyboardButton("720p", callback_data='720'),
             InlineKeyboardButton("1080p", callback_data='1080')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Qaysi sifatda yuklab olishni xohlaysiz?", reply_markup=reply_markup)
    else:
        await download_and_send(query, context, 'audio')

async def quality_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    quality = query.data
    await download_and_send(query, context, 'video', quality)

async def download_and_send(query, context, format_type, quality=None):
    video_url = context.user_data.get('video_url')
    if not video_url:
        await query.edit_message_text("Xatolik! URL topilmadi.")
        return
    
    await query.edit_message_text("Video yuklab olinmoqda, iltimos kuting...")
    video_path = download_youtube_video(video_url, format_type, quality)
    
    with open(video_path, 'rb') as file:
        if format_type == 'video':
            await query.message.reply_video(file)
        else:
            await query.message.reply_audio(file)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_video))
    application.add_handler(CallbackQueryHandler(platform_handler, pattern='^(instagram|youtube)$'))
    application.add_handler(CallbackQueryHandler(format_handler, pattern='^(video|audio)$'))
    application.add_handler(CallbackQueryHandler(quality_handler, pattern='^(144|360|720|1080)$'))
    
    application.run_polling()

if __name__ == "__main__":
    main()
