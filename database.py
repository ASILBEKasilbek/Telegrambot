import sqlite3
from datetime import datetime, timedelta


def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, requests INTEGER, join_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins 
                 (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels 
                 (chat_id TEXT PRIMARY KEY, type TEXT)''')  # type: "channel" yoki "group"
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, requests, join_date) VALUES (?, 0, ?)",
              (user_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def update_request_count(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET requests = requests + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", 
              (datetime.now().strftime("%Y-%m-%d"),))
    daily = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE join_date LIKE ?", 
              (datetime.now().strftime("%Y-%m") + "%",))
    monthly = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users")
    yearly = c.fetchone()[0]
    conn.close()
    return daily, monthly, yearly

def get_users():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, requests FROM users")
    users = c.fetchall()
    conn.close()
    return users

def add_admin(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_admins():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    admins = c.fetchall()
    conn.close()
    return [admin[0] for admin in admins]

def remove_admin(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_channel(chat_id, chat_type):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO channels (chat_id, type) VALUES (?, ?)", (chat_id, chat_type))
    conn.commit()
    conn.close()

def remove_channel(chat_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def get_channels():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT chat_id, type FROM channels")
    channels = c.fetchall()
    conn.close()
    return channels

# Bugungi yangi qo'shilgan foydalanuvchilar soni
def get_new_users_today():
    today = datetime.now().date()
    # Misol uchun: users jadvalidan bugungi sana bo'yicha foydalanuvchilarni sanash
    return len([user for user in users if user["join_date"].date() == today])

# Aktiv foydalanuvchilar soni (oxirgi 24 soat ichida faol bo'lganlar)
def get_active_users():
    last_24_hours = datetime.now() - timedelta(hours=24)
    # Misol uchun: users jadvalidan oxirgi 24 soat ichida faol bo'lgan foydalanuvchilarni sanash
    return len([user for user in users if user["last_activity"] >= last_24_hours])

# Bloklangan foydalanuvchilar soni
def get_blocked_users():
    # Misol uchun: users jadvalidan bloklangan foydalanuvchilarni sanash
    return len([user for user in users if user["is_blocked"]])