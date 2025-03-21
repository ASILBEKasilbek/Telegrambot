import os
import tempfile
import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Importlar
from config import ADMIN_IDS
from database import (
    add_user, update_request_count, get_stats, get_users, add_admin, get_admins, remove_admin,
    add_channel, remove_channel, get_channels
)
from utils import (
    download_social_media_video, process_youtube_video, shazam_video, shazam_audio,
    check_membership, download_mp3_from_youtube
)

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL qisqartirish uchun yordamchi funksiya
def shorten_url(long_url):
    response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
    return response.text if response.status_code == 200 else long_url

# Fayl yuborish uchun umumiy funksiya
async def send_file(update, file_path, reply_func, **kwargs):
    if os.path.getsize(file_path) / (1024 * 1024) < 50:
        with open(file_path, "rb") as f:
            await reply_func(f, **kwargs)
    else:
        await update.message.reply_text("Fayl hajmi 50 MB’dan katta, yuklash mumkin emas!")

# Start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    if not await check_membership(context.bot, user_id):
        channels = get_channels()
        if not channels:
            await update.message.reply_text("Botni ishlatish uchun hech qanday kanal qo‘shilmagan. Admin bilan bog‘laning!")
            return
        
        keyboard = [
            [InlineKeyboardButton(f"{chat_type.capitalize()}: {chat_id[1:] if chat_id.startswith('@') else chat_id}", url=f"https://t.me/{chat_id[1:] if chat_id.startswith('@') else chat_id}")]
            for chat_id, chat_type in channels
        ]
        keyboard.append([InlineKeyboardButton("Tekshirish", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Botdan foydalanish uchun quyidagi kanal va guruhlarga a'zo bo‘lishingiz shart:",
            reply_markup=reply_markup
        )
        return
    await update.message.reply_text("Salom! Botdan foydalanish uchun:\n- YouTube yoki boshqa video URL yuboring.\n- Video yoki audio fayl yuklang.\nAdminlar uchun: /admin")

# Tekshirish tugmasi uchun callback
async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if await check_membership(context.bot, user_id):
        await query.edit_message_text("Tabriklaymiz! Endi botdan to‘liq foydalanishingiz mumkin.\n/start ni qayta bosing.")
    else:
        await query.edit_message_text("Siz hali barcha kanal va guruhlarga a'zo bo‘lmagansiz. Iltimos, obuna bo‘ling va qayta tekshiring.")

# URL handler
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Botdan foydalanish uchun barcha kanal va guruhlarga a'zo bo‘ling!")
        return
    url = update.message.text.strip()
    update_request_count(user_id)
    logger.info(f"Handling URL from user {user_id}: {url}")

    if not url.startswith("http"):
        await update.message.reply_text("Iltimos, to‘g‘ri URL yuboring (masalan, https://...)!")
        return

    await update.message.reply_text("Video qayta ishlanmoqda...")
    try:
        if "youtube.com" in url or "youtu.be" in url:
            result = process_youtube_video(url)
            if isinstance(result, str) and result.startswith("downloads/") and os.path.exists(result):
                await send_file(update, result, update.message.reply_video)
                os.remove(result)
            elif isinstance(result, str) and result.startswith("http"):
                short_url = shorten_url(result)
                keyboard = [[InlineKeyboardButton("Yuklab olish", url=short_url)]]
                await update.message.reply_text("Video hajmi katta!", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text("YouTube videosida xatolik!")
        elif "instagram.com" in url:
            result = download_social_media_video(url)
            if result:
                await update.message.reply_video(result)
            else:
                await update.message.reply_text("Instagram videosida xatolik!")
        else:
            await update.message.reply_text("Faqat YouTube yoki Instagram URL’lari qo‘llab-quvvatlanadi!")
    except Exception as e:
        logger.error(f"URL handling error: {e}")
        await update.message.reply_text(f"Xatolik: {str(e)}")

# Video handler
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Botdan foydalanish uchun barcha kanal va guruhlarga a'zo bo‘ling!")
        return
    update_request_count(user_id)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        file_path = temp_file.name
        try:
            file = await update.message.video.get_file()
            await file.download_to_drive(file_path)

            await update.message.reply_text("Qo‘shiq aniqlanmoqda...")
            title, artist = await shazam_video(file_path)

            if title and artist:
                await update.message.reply_text(f"Qo‘shiq topildi!\nNomi: {title}\nIjrochi: {artist}\nMP3 yuklanmoqda...")
                mp3_path = download_mp3_from_youtube(f"{title} {artist}")
                if mp3_path and os.path.exists(mp3_path):
                    await send_file(update, mp3_path, update.message.reply_audio, title=title, performer=artist)
                    os.remove(mp3_path)
                else:
                    await update.message.reply_text("MP3 yuklab olinmadi!")
            else:
                await update.message.reply_text("Videoda qo‘shiq topilmadi.")
        except Exception as e:
            logger.error(f"Video handling error: {e}")
            await update.message.reply_text(f"Xatolik: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# Audio handler
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_membership(context.bot, user_id):
        await update.message.reply_text("Botdan foydalanish uchun barcha kanal va guruhlarga a'zo bo‘ling!")
        return
    update_request_count(user_id)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        file_path = temp_file.name
        try:
            file = await update.message.audio.get_file()
            await file.download_to_drive(file_path)

            await update.message.reply_text("Qo‘shiq aniqlanmoqda...")
            title, artist = await shazam_audio(file_path)

            if title and artist:
                await update.message.reply_text(f"Qo‘shiq topildi!\nNomi: {title}\nIjrochi: {artist}\nMP3 yuklanmoqda...")
                mp3_path = download_mp3_from_youtube(f"{title} {artist}")
                if mp3_path and os.path.exists(mp3_path):
                    await send_file(update, mp3_path, update.message.reply_audio, title=title, performer=artist)
                    os.remove(mp3_path)
                else:
                    await update.message.reply_text("MP3 yuklab olinmadi!")
            else:
                await update.message.reply_text("Audioda qo‘shiq topilmadi.")
        except Exception as e:
            logger.error(f"Audio handling error: {e}")
            await update.message.reply_text(f"Xatolik: {str(e)}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return

    keyboard = [
        [KeyboardButton("📊 Statistika")],
        [KeyboardButton("👤 Foydalanuvchilar")],
        [KeyboardButton("📋 Adminlar")],
        [KeyboardButton("➕ Admin qo'shish"), KeyboardButton("➖ Admin o'chirish")],
        [KeyboardButton("📢 Reklama yuborish")],
        [KeyboardButton("➕ Kanal qo'shish"), KeyboardButton("➖ Kanal o'chirish")],
        [KeyboardButton("📋 Kanallar ro'yxati")],
        [KeyboardButton("🔙 Orqaga")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🛠 **Admin Paneli**: Tugmalardan birini tanlang:", reply_markup=reply_markup)

# Statistika (boyitilgan)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        daily, monthly, yearly = get_stats()
        total_users = len(get_users())
        users = get_users()
        active_users = sorted(users, key=lambda x: x[1], reverse=True)[:5]  # Eng faol 5 foydalanuvchi
        
        text = (
            f"📊 **Statistika**:\n"
            f"• Kunlik so'rovlar: {daily}\n"
            f"• Oylik so'rovlar: {monthly}\n"
            f"• Yillik so'rovlar: {yearly}\n"
            f"• Umumiy foydalanuvchilar: {total_users}\n"
            f"• Eng faol foydalanuvchilar:\n"
        )
        for i, (user_id, req_count) in enumerate(active_users, 1):
            text += f"  {i}. ID: {user_id} - {req_count} so'rov\n"
        
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text("❌ Statistika yuklanmadi.")

# Foydalanuvchilar ro'yxati
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_users()
    if not users:
        await update.message.reply_text("ℹ️ Foydalanuvchilar topilmadi.")
        return
    text = "👤 **Foydalanuvchilar ro'yxati**:\n" + "\n".join(f"• ID: {user[0]}, So'rovlar: {user[1]}" for user in users)
    await update.message.reply_text(text[:4000])

# Adminlar ro'yxati
async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = get_admins()
    if not admins:
        await update.message.reply_text("ℹ️ Adminlar ro'yxati bo'sh.")
        return
    text = "📋 **Adminlar ro'yxati**:\n" + "\n".join(f"• ID: {admin}" for admin in admins)
    await update.message.reply_text(text)

# Admin qo'shish
async def add_admin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    await update.message.reply_text("➕ **Admin qo'shish**: Yangi admin ID'sini yuboring.")
    context.user_data["state"] = "add_admin"

async def add_admin_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    new_admin_id = update.message.text.strip()
    if not new_admin_id.isdigit():
        await update.message.reply_text("❌ Faqat raqam yuboring!")
        return
    new_admin_id = int(new_admin_id)
    if new_admin_id in get_admins():
        await update.message.reply_text(f"ℹ️ {new_admin_id} allaqachon admin!")
        return
    add_admin(new_admin_id)
    await update.message.reply_text(f"✅ Admin {new_admin_id} qo'shildi.")
    context.user_data.clear()

# Admin o'chirish
async def remove_admin_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    await update.message.reply_text("➖ **Admin o'chirish**: O'chiriladigan admin ID'sini yuboring.")
    context.user_data["state"] = "remove_admin"

async def remove_admin_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    admin_id = update.message.text.strip()
    if not admin_id.isdigit():
        await update.message.reply_text("❌ Faqat raqam yuboring!")
        return
    admin_id = int(admin_id)
    if admin_id not in get_admins():
        await update.message.reply_text(f"ℹ️ {admin_id} adminlar ro'yxatida yo'q!")
        return
    remove_admin(admin_id)
    await update.message.reply_text(f"✅ Admin {admin_id} o'chirildi.")
    context.user_data.clear()

# Reklama yuborish
async def send_ad_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    await update.message.reply_text(
        "📢 **Reklama yuborish**: Reklama xabarini yuboring (matn, rasm, video yoki audio)."
    )
    context.user_data["state"] = "send_ad"

async def send_ad_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    if context.user_data.get("state") != "send_ad":
        return

    msg = update.message
    users = get_users()
    if not users:
        await update.message.reply_text("ℹ️ Foydalanuvchilar topilmadi.")
        return

    success_count = 0
    total_users = len(users)
    for user in users:
        try:
            if msg.text:
                await context.bot.send_message(chat_id=user[0], text=msg.text)
            elif msg.photo:
                await context.bot.send_photo(chat_id=user[0], photo=msg.photo[-1].file_id, caption=msg.caption or "")
            elif msg.video:
                await context.bot.send_video(chat_id=user[0], video=msg.video.file_id, caption=msg.caption or "")
            elif msg.audio:
                await context.bot.send_audio(chat_id=user[0], audio=msg.audio.file_id, caption=msg.caption or "")
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Ad send error for user {user[0]}: {e}")
            continue

    await update.message.reply_text(f"✅ Reklama {success_count}/{total_users} foydalanuvchiga yuborildi!")
    context.user_data.clear()

# Kanal qo'shish (yaxshilangan)
async def add_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    await update.message.reply_text("➕ **Kanal qo'shish**: Kanal nomini (@ bilan yoki ID sifatida) yuboring.")
    context.user_data["state"] = "add_channel"

async def add_channel_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    channel = update.message.text.strip()
    
    # Agar @ bilan boshlanmasa, shunchaki ID sifatida qabul qilamiz
    if not channel.startswith("@"):
        channel = channel  # ID sifatida saqlanadi
    if channel in [c[0] for c in get_channels()]:
        await update.message.reply_text(f"ℹ️ {channel} allaqachon qo'shilgan!")
        return
    add_channel(channel, "channel")
    await update.message.reply_text(f"✅ Kanal {channel} qo'shildi.")
    context.user_data.clear()

# Kanal o'chirish
async def remove_channel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    await update.message.reply_text("➖ **Kanal o'chirish**: O'chiriladigan kanal nomini yuboring.")
    context.user_data["state"] = "remove_channel"

async def remove_channel_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id not in get_admins():
        await update.message.reply_text("⚠️ Siz admin emassiz!")
        return
    channel = update.message.text.strip()
    if channel not in [c[0] for c in get_channels()]:
        await update.message.reply_text(f"ℹ️ {channel} ro'yxatda yo'q!")
        return
    remove_channel(channel)
    await update.message.reply_text(f"✅ Kanal {channel} o'chirildi.")
    context.user_data.clear()

# Kanallar ro'yxati
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = get_channels()
    if not channels:
        await update.message.reply_text("ℹ️ Kanallar ro'yxati bo'sh.")
        return
    text = "📋 **Kanallar ro'yxati**:\n" + "\n".join(f"• {channel[0]}" for channel in channels)
    await update.message.reply_text(text)

# Matnli xabarlarni boshqarish
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if user_id in ADMIN_IDS or user_id in get_admins():
        if text == "📊 Statistika":
            await stats(update, context)
        elif text == "👤 Foydalanuvchilar":
            await list_users(update, context)
        elif text == "📋 Adminlar":
            await list_admins(update, context)
        elif text == "➕ Admin qo'shish":
            await add_admin_prompt(update, context)
        elif text == "➖ Admin o'chirish":
            await remove_admin_prompt(update, context)
        elif text == "📢 Reklama yuborish":
            await send_ad_prompt(update, context)
        elif text == "➕ Kanal qo'shish":
            await add_channel_prompt(update, context)
        elif text == "➖ Kanal o'chirish":
            await remove_channel_prompt(update, context)
        elif text == "📋 Kanallar ro'yxati":
            await list_channels(update, context)
        elif text == "🔙 Orqaga":
            await admin_panel(update, context)
        elif context.user_data.get("state") == "add_admin":
            await add_admin_execute(update, context)
        elif context.user_data.get("state") == "remove_admin":
            await remove_admin_execute(update, context)
        elif context.user_data.get("state") == "send_ad":
            await send_ad_execute(update, context)
        elif context.user_data.get("state") == "add_channel":
            await add_channel_execute(update, context)
        elif context.user_data.get("state") == "remove_channel":
            await remove_channel_execute(update, context)
        return

    await handle_url(update, context)

# Handlerlarni ro'yxatdan o'tkazish
def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO, send_ad_execute))
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="check_membership"))