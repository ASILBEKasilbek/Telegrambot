# 📥 Social Media Downloader Bot

Bu **Telegram bot** ijtimoiy tarmoqlardan **videolarni yuklab olish**, **Shazam orqali musiqa topish** va **YouTube videolarni yuklash** imkoniyatini beradi.

## ✨ Asosiy imkoniyatlar
✅ **Ijtimoiy tarmoqlardan video yuklash**: TikTok, Instagram, Facebook va boshqa platformalarni qo‘llab-quvvatlaydi.  
✅ **YouTube videolarni yuklash**: YouTube-dan video yoki audio shaklda yuklab olish mumkin.  
✅ **Shazam funksiyasi**: Audio fayl yuborsangiz, uning nomi va ijrochisini topib beradi.  
✅ **Foydalanish oson**: Telegram bot orqali bir nechta tugmalar bilan ishlaydi.

---
## 📌 O‘rnatish

### 1️⃣ Talablar
Quyidagi dasturlar o‘rnatilgan bo‘lishi kerak:
- **Python** (3.10 yoki yuqori versiya)
- **pip** (Python paket menejeri)
- **ffmpeg** (YouTube videolarni yuklash uchun kerak)

Linux/Mac uchun **ffmpeg** ni o‘rnatish:
```bash
sudo apt install ffmpeg
```
Windows uchun **Chocolatey** orqali:
```bash
choco install ffmpeg
```

---
## 🚀 Ishga tushirish

### 2️⃣ Virtual muhit yaratish
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3️⃣ Kerakli kutubxonalarni o‘rnatish
```bash
pip install -r requirements.txt
```

### 4️⃣ `.env` faylini yaratish
Botni xavfsiz ishlatish uchun `.env` faylini yaratib, quyidagi ma’lumotlarni kiriting:
```plaintext
BOT_TOKEN=your-telegram-bot-token
```

### 5️⃣ Botni ishga tushirish
```bash
python main.py
```

---
## 🐳 Docker orqali o‘rnatish

### 1️⃣ **`Dockerfile` yaratish**
📄 **`Dockerfile`** fayli:
```dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### 2️⃣ **Docker konteynerini yaratish va ishga tushirish**
```bash
docker build -t telegram-bot .
docker run -d --name social_bot --env-file .env telegram-bot
```

Agar xatolik yuzaga kelsa, loglarni tekshiring:
```bash
docker logs social_bot
```

---
## 🌍 Railway yoki Serverga joylash

Agar botni Railway yoki boshqa serverga joylamoqchi bo‘lsangiz:
1️⃣ **Railway-da yangi loyiha yarating**
2️⃣ **GitHub-ga kodni yuklang**
3️⃣ Railway dagi **Deploy** tugmasini bosing
4️⃣ **Environment Variables (Muhit o‘zgaruvchilari)** bo‘limiga `BOT_TOKEN` ni qo‘shing

---
## 📞 Aloqa
Agar sizga yordam kerak bo‘lsa yoki takliflaringiz bo‘lsa, Telegram orqali bog‘laning: [@dasturch1_asilbek]

