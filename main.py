from flask import Flask
from threading import Thread
import sqlite3
import random
import time
import logging
import base64
import hmac
import hashlib
import struct
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= 24/7 Flask Keep Alive =================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ================= Logging & Config =================
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8610842156:AAHHrhITZxfQReYUATIN87MBGouRIIwajbM"
ADMIN_ID = 8791376128
ADMIN_USERNAME = "sowrov0134"

TELEGRAM_CHANNEL_USERNAME = "@smearnin013"
OTP_CHANNEL_USERNAME = "@sowrov536"

TELEGRAM_CHANNEL = "https://t.me/smearnin013"
OTP_BOT_LINK = "https://t.me/sowrov536"
YOUTUBE_LINK = "https://youtube.com/@smearning2026"

OTP_RATE = 0.20
REFERRAL_BONUS = 10.0
MIN_WITHDRAW = 120.0
MIN_VALID_REFERS = 3

DB_FILE = "bot_database.db"

# ================= Database Initialization =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY, 
                        username TEXT,
                        balance REAL DEFAULT 0.0, 
                        success_otps INTEGER DEFAULT 0, 
                        referred_by INTEGER DEFAULT NULL, 
                        valid_refers INTEGER DEFAULT 0, 
                        claimed_refers TEXT DEFAULT "",
                        is_banned INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS verified (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS api_panels (
                        panel_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        panel_name TEXT,
                        api_url TEXT,
                        api_token TEXT,
                        status TEXT DEFAULT 'ON'
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()

# ================= Helper Functions =================
def get_setting(key, default):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def is_maintenance_mode():
    return get_setting("maintenance", "OFF") == "ON"

def get_user_data(user_id, username=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, success_otps, referred_by, valid_refers, claimed_refers, username, is_banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, username, balance, success_otps, referred_by, valid_refers, claimed_refers, is_banned) VALUES (?, ?, 0.0, 0, NULL, 0, '', 0)", (user_id, username))
        conn.commit()
        data = {"balance": 0.0, "success_otps": 0, "referred_by": None, "valid_refers": 0, "claimed_refers": set(), "username": username, "is_banned": 0}
    else:
        claimed = [int(x) for x in row[4].split(",") if x.strip()]
        data = {"balance": row[0], "success_otps": row[1], "referred_by": row[2], "valid_refers": row[3], "claimed_refers": set(claimed), "username": row[5], "is_banned": row[6]}
        if username and row[5] != username:
            cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
            conn.commit()
    conn.close()
    return data

def save_user_data(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    claimed_str = ",".join([str(x) for x in data["claimed_refers"]])
    cursor.execute("UPDATE users SET balance = ?, success_otps = ?, referred_by = ?, valid_refers = ?, claimed_refers = ?, is_banned = ? WHERE user_id = ?", 
                   (data["balance"], data["success_otps"], data["referred_by"], data["valid_refers"], claimed_str, data["is_banned"], user_id))
    conn.commit()
    conn.close()

def is_verified(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM verified WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def add_verified(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO verified (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_reply_keyboard(user_id):
    keyboard = [
        [KeyboardButton("📞 Get Number"), KeyboardButton("👛 Wallet")],
        [KeyboardButton("👥 Invite Friends"), KeyboardButton("🚦 Live Traffic")],
        [KeyboardButton("🔐 Facebook 2FA"), KeyboardButton("💬 Online Support")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("⚙️ Owner Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def generate_totp(secret):
    try:
        secret = secret.replace(" ", "").upper()
        padding = 8 - (len(secret) % 8)
        if padding < 8:
            secret += "=" * padding
        key = base64.b32decode(secret)
        counter = int(time.time() // 30)
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        o = digest[19] & 15
        code = (struct.unpack(">I", digest[o:o+4])[0] & 0x7fffffff) % 1000000
        return f"{code:06d}"
    except Exception:
        return None

def get_active_countries_from_panel():
    # ডিফল্ট কান্ট্রি লিস্ট অথবা ডায়নামিক ডাটাবেজ থেকে আনতে পারেন
    return [
        {"name": "🇹🇿 তানজানিয়া (Tanzania)", "code": "tanzania"},
        {"name": "🇷🇼 রুয়ান্ডা (Rwanda)", "code": "rwanda"},
        {"name": "🇿🇼 জিম্বাবুয়ে (Zimbabwe)", "code": "zimbabwe"},
        {"name": "🇰🇪 কেনিয়া (Kenya)", "code": "kenya"},
        {"name": "🇺🇬 উগান্ডা (Uganda)", "code": "uganda"}
    ]

def generate_numbers_by_country(country_code):
    prefix = "+255" if country_code == "tanzania" else "+250"
    numbers = []
    for _ in range(3):
        middle = "".join([str(random.randint(0, 9)) for _ in range(3)])
        end = "".join([str(random.randint(0, 9)) for _ in range(4)])
        numbers.append(f"{prefix}{random.randint(7,9)}{middle}{end}")
    return numbers

# ================= Telegram Handlers =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    user_data = get_user_data(user_id, username)
    
    if user_data["is_banned"] and user_id != ADMIN_ID:
        await update.message.reply_text("❌ দুঃখিত, আপনি এই বট ব্যবহার করার জন্য ব্যান হয়েছেন!")
        return

    if is_maintenance_mode() and user_id != ADMIN_ID:
        await update.message.reply_text("🛠 বর্তমানে বট মেইনটেন্যান্স মোডে আছে। দয়া করে কিছুক্ষণ পর চেষ্টা করুন।")
        return

    context.user_data.clear()
    
    if context.args and user_data["referred_by"] is None:
        try:
            ref_id = int(context.args[0])
            if ref_id != user_id:
                user_data["referred_by"] = ref_id
                save_user_data(user_id, user_data)
        except ValueError:
            pass

    if is_verified(user_id):
        await update.message.reply_text("👋 আমাদের নাম্বার বটে স্বাগতম!\n\nনিচের কিবোর্ড মেনু থেকে আপনার প্রয়োজনীয় সার্ভিসটি বেছে নিন:", reply_markup=get_reply_keyboard(user_id))
        return

    buttons = [
        [InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton("🤖 Telegram OTP Channel", url=OTP_BOT_LINK)],
        [InlineKeyboardButton("▶️ Subscribe YouTube", url=YOUTUBE_LINK)],
        [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")]
    ]
    await update.message.reply_text("⚠️ বটটি ব্যবহার করতে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে!\n\nজয়েন করার পর Verify বাটনে চাপ দিন।", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or query.from_user.first_name
    wallet = get_user_data(user_id, username)

    if data == "check_join":
        try:
            channel_member = await context.bot.get_chat_member(chat_id=TELEGRAM_CHANNEL_USERNAME, user_id=user_id)
            otp_member = await context.bot.get_chat_member(chat_id=OTP_CHANNEL_USERNAME, user_id=user_id)
            allowed_status = ['member', 'administrator', 'creator']
            if channel_member.status not in allowed_status or otp_member.status not in allowed_status:
                await query.answer("❌ আপনি এখনো উভয় চ্যানেল/গ্রুপে জয়েন করেননি! আগে জয়েন করুন।", show_alert=True)
                return
        except Exception as e:
            logging.error(f"Membership check error: {e}")
            await query.answer("❌ মেম্বারশিপ চেক করতে সমস্যা হয়েছে। দয়া করে চ্যানেলে জয়েন করে আবার চেষ্টা করুন।", show_alert=True)
            return

        add_verified(user_id)
        await query.answer("✅ ভেরিফিকেশন সফল হয়েছে!", show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.reply_text("👋 ভেরিফিকেশন সফল! নিচের কিবোর্ড থেকে আপনার প্রয়োজনীয় সার্ভিসটি বেছে নিন:", reply_markup=get_reply_keyboard(user_id))

    elif data == "buy_fb":
        msg = "📘 ফেসবুক সার্ভিস ক্যাটাগরি সিলেক্ট করুন:"
        btn = [
            [InlineKeyboardButton("🔹 New Facebook", callback_data="sub_new_facebook")],
            [InlineKeyboardButton("💻 PC Clone", callback_data="sub_pc_clone")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_services")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif data in ["sub_new_facebook", "sub_pc_clone"]:
        sub_type = "New Facebook" if "new" in data else "PC Clone"
        context.user_data["sub_type"] = sub_type
        
        active_countries = get_active_countries_from_panel()
        msg = f"🌍 {sub_type} এর জন্য বর্তমানে যে দেশগুলোতে ভালো ওটিপি আসছে:\n\nএকটি দেশ সিলেক্ট করুন:"
        btn = []
        for country in active_countries:
            btn.append([InlineKeyboardButton(country["name"], callback_data=f"country_{country['code']}")])
        btn.append([InlineKeyboardButton("🔙 Back", callback_data="buy_fb")])
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif data.startswith("country_"):
        c_code = data.replace("country_", "")
        context.user_data["selected_country"] = c_code
        
        nums = generate_numbers_by_country(c_code)
        sub_type = context.user_data.get("sub_type", "New Facebook")
        
        msg = (f"✅ {sub_type} এর নাম্বারগুলো রেডি!\n\n"
               f"📞 ১. `{nums[0]}`\n"
               f"📞 ২. `{nums[1]}`\n"
               f"📞 ৩. `{nums[2]}`\n\n"
               f"কোড দেখতে নিচের **Check OTP** এ ক্লিক করুন।")
        
        sub_callback = "sub_new_facebook" if sub_type == "New Facebook" else "sub_pc_clone"
        
        btn = [
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"country_{c_code}")],
            [InlineKeyboardButton("📩 Check OTP", url=OTP_BOT_LINK), InlineKeyboardButton("🌍 Change Country", callback_data=sub_callback)],
            [InlineKeyboardButton("🔙 Back", callback_data=sub_callback)]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "back_to_services":
        services = [
            [InlineKeyboardButton("📘 Facebook", callback_data="buy_fb"), InlineKeyboardButton("🟢 WhatsApp", callback_data="buy_wa")],
            [InlineKeyboardButton("✈️ Telegram", callback_data="buy_tg"), InlineKeyboardButton("🟡 IMO", callback_data="buy_imo")],
            [InlineKeyboardButton("📸 Instagram", callback_data="buy_insta")]
        ]
        await query.edit_message_text("📱 যে সার্ভিসের নাম্বার দরকার বেছে নিন:", reply_markup=InlineKeyboardMarkup(services))

    elif data.startswith("buy_"):
        service_name = data.replace("buy_", "").upper()
        active_countries = get_active_countries_from_panel()
        msg = f"🌍 {service_name} এর জন্য বর্তমানে যে দেশগুলোতে ভালো ওটিপি আসছে:\n\nএকটি দেশ সিলেক্ট করুন:"
        btn = []
        for country in active_countries:
            btn.append([InlineKeyboardButton(country["name"], callback_data=f"country_{country['code']}")])
        btn.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_services")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif data.startswith("withdraw_"):
        method = data.replace("withdraw_", "")
        if wallet['balance'] < MIN_WITHDRAW:
            await query.answer(f"❌ সর্বনিম্ন উইথড্র ৳{MIN_WITHDRAW}!", show_alert=True)
            return
        context.user_data['state'] = "waiting_for_withdraw_acc"
        context.user_data['withdraw_method'] = method
        btn = [[InlineKeyboardButton("🔙 Cancel", callback_data="wallet_back")]]
        await query.edit_message_text(f"📱 আপনার {method} নাম্বারটি লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "wallet_back":
        msg = f"👛 ওয়ালেট বিবরণী:\n\n💰 ব্যালেন্স: ৳{wallet['balance']:.2f}\n📥 সফল ওটিপি: {wallet['success_otps']}\n👥 রেফার: {wallet['valid_refers']} / {MIN_VALID_REFERS}"
        btn = [
            [InlineKeyboardButton("💖 বিকাশ", callback_data="withdraw_bKash"), InlineKeyboardButton("🟠 নগদ", callback_data="withdraw_Nagad")],
            [InlineKeyboardButton("🔵 রকেট", callback_data="withdraw_Rocket"), InlineKeyboardButton("🟡 বাইনান্স", callback_data="withdraw_Binance")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    # ================= Admin Panel Callbacks =================
    elif data == "admin_stats" and user_id == ADMIN_ID:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, balance FROM users")
        users = cursor.fetchall()
        conn.close()
        
        text = f"📊 মোট ইউজার: {len(users)} জন\n\n👤 ইউজার লিস্ট (UID & Username):\n"
        for u in users:
            uname = f"@{u[1]}" if u[1] else "No Username"
            text += f"• `{u[0]}` | {uname} | ৳{u[2]:.2f}\n"
        if len(text) > 4000:
            text = text[:4000] + "\n... (লিস্ট অনেক বড়)"

        btn = [
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "admin_panels_mgmt" and user_id == ADMIN_ID:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT panel_id, panel_name, status FROM api_panels")
        panels = cursor.fetchall()
        conn.close()

        text = "🔧 **ডাইনামিক নাম্বার প্যানেল ম্যানেজমেন্ট:**\n\nনিচের প্যানেলগুলো বর্তমানে ডাটাবেজে রয়েছে:\n"
        btn = []
        if panels:
            for p in panels:
                text += f"• ID: `{p[0]}` | নাম: **{p[1]}** | স্ট্যাটাস: `{p[2]}`\n"
                btn.append([InlineKeyboardButton(f"❌ ডিলিট: {p[1]}", callback_data=f"del_panel_{p[0]}")])
        else:
            text += "কোনো প্যানেল যুক্ত করা হয়নি!\n"

        btn.append([InlineKeyboardButton("➕ নতুন প্যানেল যোগ করুন", callback_data="add_panel_prompt")])
        btn.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "add_panel_prompt" and user_id == ADMIN_ID:
        context.user_data['state'] = "waiting_for_new_panel"
        btn = [[InlineKeyboardButton("🔙 Cancel", callback_data="admin_panels_mgmt")]]
        await query.edit_message_text("✍️ নতুন প্যানেল যোগ করতে এই ফরম্যাটে লিখে পাঠান:\n\n`প্যানেলের_নাম | API_URL | API_Token`\nউদাহরণ: `MyPanel | https://api.example.com | token123`", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data.startswith("del_panel_") and user_id == ADMIN_ID:
        pid = int(data.replace("del_panel_", ""))
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_panels WHERE panel_id = ?", (pid,))
        conn.commit()
        conn.close()
        await query.answer("✅ প্যানেল সফলভাবে ডিলিট করা হয়েছে!", show_alert=True)
        # রিফ্রেশ প্যানেল লিস্ট
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT panel_id, panel_name, status FROM api_panels")
        panels = cursor.fetchall()
        conn.close()
        text = "🔧 **ডাইনামিক নাম্বার প্যানেল ম্যানেজমেন্ট:**\n\n"
        btn = []
        for p in panels:
            text += f"• ID: `{p[0]}` | নাম: **{p[1]}** | স্ট্যাটাস: `{p[2]}`\n"
            btn.append([InlineKeyboardButton(f"❌ ডিলিট: {p[1]}", callback_data=f"del_panel_{p[0]}")])
        btn.append([InlineKeyboardButton("➕ নতুন প্যানেল যোগ করুন", callback_data="add_panel_prompt")])
        btn.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "admin_maintenance" and user_id == ADMIN_ID:
        current = get_setting("maintenance", "OFF")
        new_status = "OFF" if current == "ON" else "ON"
        set_setting("maintenance", new_status)
        await query.answer(f"✅ মেইনটেন্যান্স মোড এখন: {new_status}", show_alert=True)
        # রিফ্রেশ অ্যাডমিন হোম
        await admin_home_panel(query.message, edit=True)

    elif data == "admin_home" and user_id == ADMIN_ID:
        await admin_home_panel(query.message, edit=True)

    elif data == "admin_manage_bal" and user_id == ADMIN_ID:
        context.user_data['state'] = "waiting_for_admin_bal_action"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]
        await query.edit_message_text("✍️ ব্যালেন্স অ্যাড বা মাইনাস করতে এই ফরম্যাটে লিখুন:\n\n`[UID] [+ অথবা -] [টাকা]`\nউদাহরণ: `123456789 +50` অথবা `123456789 -20`", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "admin_broadcast" and user_id == ADMIN_ID:
        context.user_data['state'] = "waiting_for_broadcast_msg"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]
        await query.edit_message_text("📢 সকল ইউজারের কাছে পাঠানোর জন্য মেসেজটি লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "admin_ban_unban" and user_id == ADMIN_ID:
        context.user_data['state'] = "waiting_for_ban_action"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]
        await query.edit_message_text("🚫 ইউজারকে ব্যান বা আনব্যান করতে ইউজার আইডি লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "back_main":
        context.user_data.clear()
        try:
            await query.message.delete()
        except Exception:
   
