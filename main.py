from flask import Flask
from threading import Thread
import sqlite3

# --- Render 24/7 Keep Alive Server ---
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

# --- Bot Code ---
import logging
import base64
import hmac
import hashlib
import struct
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= সেটআপ তথ্য =================
BOT_TOKEN = "8610842156:AAF03CmhwZX4h16lDx_zODCLRuH_iCexf7o"

ADMIN_ID = 8791376128                            # আপনার এডমিন আইডি
ADMIN_USERNAME = "sowrov0134"                       # সাপোর্টের জন্য আপনার ইউজারনেম

TELEGRAM_CHANNEL = "https://t.me/sowrov0134"
OTP_BOT_LINK = "https://t.me/otp_bot_536"
YOUTUBE_LINK = "https://youtube.com/@smearning2026?si=Txul4qaB4tS0-TkY"

OTP_RATE = 0.20           # প্রতি ওটিপিতে ২০ পয়সা
REFERRAL_BONUS = 10.0     # সফল রেফারে ১০ টাকা
MIN_WITHDRAW = 120.0      # মিনিমাম উইথড্র ১২০ টাকা
MIN_REFERRED_OTPS = 50    # যাকে রেফার করা হয়েছে তার মিনিমাম ওটিপি শর্ত
MIN_VALID_REFERS = 3      # উইথড্র করার জন্য মিনিমাম সফল রেফার
# ===============================================

DB_FILE = "bot_database.db"

# SQLite ডাটাবেজ এবং টেবিল তৈরি
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            success_otps INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL,
            valid_refers INTEGER DEFAULT 0,
            claimed_refers TEXT DEFAULT ""
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verified (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ইউজার ডাটা ফেচ বা তৈরি করার ফাংশন
def get_user_data(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, success_otps, referred_by, valid_refers, claimed_refers FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance, success_otps, referred_by, valid_refers, claimed_refers) VALUES (?, 0.0, 0, NULL, 0, '')", (user_id,))
        conn.commit()
        user_data = {
            "balance": 0.0,
            "success_otps": 0,
            "referred_by": None,
            "valid_refers": 0,
            "claimed_refers": set()
        }
    else:
        claimed_list = [int(x) for x in row[4].split(",") if x.strip()]
        user_data = {
            "balance": row[0],
            "success_otps": row[1],
            "referred_by": row[2],
            "valid_refers": row[3],
            "claimed_refers": set(claimed_list)
        }
    conn.close()
    return user_data

# ইউজার ডাটা আপডেট সেভ করার ফাংশন
def save_user_data(user_id, user_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    claimed_str = ",".join([str(x) for x in user_data["claimed_refers"]])
    cursor.execute('''
        UPDATE users SET balance = ?, success_otps = ?, referred_by = ?, valid_refers = ?, claimed_refers = ?
        WHERE user_id = ?
    ''', (user_data["balance"], user_data["success_otps"], user_data["referred_by"], user_data["valid_refers"], claimed_str, user_id))
    conn.commit()
    conn.close()

# ভেরিফাইড ইউজার চেক ও সেভ
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

# কিবোর্ডে যে মেনু বাটনগুলো দেখাবে
def get_reply_keyboard(user_id):
    keyboard = [
        [KeyboardButton("📞 Get Number"), KeyboardButton("👛 Wallet")],
        [KeyboardButton("👥 Invite Friends"), KeyboardButton("🚦 Live Traffic")],
        [KeyboardButton("🔐 Facebook 2FA"), KeyboardButton("💬 Online Support")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton("⚙️ Owner Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 2FA (TOTP) জেনারেটর
def generate_totp(secret):
    try:
        secret = secret.replace(" ", "").upper()
        padding = 8 - (len(secret) % 8)
        if padding < 8:
            secret += "=" * padding
        
        key = base64.b32decode(secret)
        import time
        counter = int(time.time() // 30)
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        o = digest[19] & 15
        code = (struct.unpack(">I", digest[o:o+4])[0] & 0x7fffffff) % 1000000
        return f"{code:06d}"
    except Exception:
        return None

# মূল মেনু দেখানোর ফাংশন
async def show_main_menu(update_or_query, context, is_edit=False):
    user_id = update_or_query.from_user.id if hasattr(update_or_query, 'from_user') else update_or_query.effective_user.id
    
    buttons = [
        [InlineKeyboardButton("🔢 Get Number", callback_data="get_number")],
        [InlineKeyboardButton("🔍 Search Number", callback_data="search_num"), InlineKeyboardButton("🚦 Live Traffic", callback_data="live_traffic")],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data="refer"), InlineKeyboardButton("👛 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("🔐 2FA Code Generator", callback_data="2fa_menu"), InlineKeyboardButton("💬 Online Support", callback_data="support")]
    ]
    
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("⚙️ Owner Admin Panel", callback_data="admin_panel")])

    text = "👋 **আমাদের নাম্বার বটে স্বাগতম!**\n\nনিচের মেনু বা কিবোর্ড থেকে আপনার প্রয়োজনীয় সার্ভিসটি বেছে নিন:"
    reply_kb = get_reply_keyboard(user_id)

    if is_edit and hasattr(update_or_query, 'edit_message_text'):
        try:
            await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        except Exception:
            pass
    else:
        target = update_or_query.message if hasattr(update_or_query, 'message') and update_or_query.message else update_or_query
        await target.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        await target.reply_text("👇 নিচ থেকেও শর্টকাট মেনু ব্যবহার করতে পারেন:", reply_markup=reply_kb)

# /start কম্যান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    context.user_data.clear()
    
    if context.args and user_data["referred_by"] is None:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:
                user_data["referred_by"] = referrer_id
                save_user_data(user_id, user_data)
        except ValueError:
            pass

    if is_verified(user_id):
        await show_main_menu(update, context, is_edit=False)
        return

    buttons = [
        [InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton("🤖 Telegram OTP Channel", url=OTP_BOT_LINK)],
        [InlineKeyboardButton("▶️ Subscribe YouTube", url=YOUTUBE_LINK)],
        [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")]
    ]
    await update.message.reply_text(
        "⚠️ **বটটি ব্যবহার করতে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে!**\n\n"
        "জয়েন শেষ হলে **Verify** বাটনে চাপ দিন।",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

# বাটন হ্যান্ডলার (Inline Buttons)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_wallet = get_user_data(user_id)

    if data == "check_join":
        add_verified(user_id)
        await query.answer("✅ ভেরিফিকেশন সফল হয়েছে!", show_alert=True)
        await show_main_menu(query, context, is_edit=True)

    elif data == "get_number":
        services = [
            [InlineKeyboardButton("📘 Facebook", callback_data="buy_fb"), InlineKeyboardButton("🟢 WhatsApp", callback_data="buy_wa")],
            [InlineKeyboardButton("✈️ Telegram", callback_data="buy_tg"), InlineKeyboardButton("🟡 IMO", callback_data="buy_imo")],
            [InlineKeyboardButton("📸 Instagram", callback_data="buy_insta")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]
        ]
        await query.edit_message_text("📱 **যে সার্ভিসের নাম্বার দরকার বেছে নিন:**", reply_markup=InlineKeyboardMarkup(services), parse_mode="Markdown")

    elif data.startswith("buy_"):
        service_name = data.replace("buy_", "").upper()
        demo_number = "+8801700000000"
        
        user_wallet["success_otps"] += 1
        user_wallet["balance"] += OTP_RATE

        referrer_id = user_wallet.get("referred_by")
        if referrer_id and user_wallet["success_otps"] >= MIN_REFERRED_OTPS:
            referrer_wallet = get_user_data(referrer_id)
            if user_id not in referrer_wallet["claimed_refers"]:
                referrer_wallet["claimed_refers"].add(user_id)
                referrer_wallet["valid_refers"] += 1
                referrer_wallet["balance"] += REFERRAL_BONUS
                save_user_data(referrer_id, referrer_wallet)
                
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 **অভিনন্দন!** আপনার রেফার করা ইউজার (`{user_id}`) ৫০টি ওটিপি সম্পন্ন করেছে。\n\n"
                             f"💰 আপনার ওয়ালেটে **৳{REFERRAL_BONUS:.2f}** যোগ হয়েছে!",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        
        save_user_data(user_id, user_wallet)

        msg = (
            f"✅ **আপনার {service_name} নাম্বার রেডি!**\n\n"
            f"📌 **সার্ভিস:** {service_name}\n"
            f"📞 **নাম্বার:** `{demo_number}`\n\n"
            f"উপরে দেওয়া নাম্বারটিতে কোড পাঠান। কোড চেক করতে নিচের বাটনে চাপ দিন।"
        )
        
        btn = [
            [InlineKeyboardButton("📩 Check OTP / Get Code", callback_data="demo_otp")],
            [InlineKeyboardButton("📢 View OTP Channel", url=OTP_BOT_LINK)],
            [InlineKeyboardButton("🔙 Back", callback_data="get_number")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "demo_otp":
        await query.answer("📩 আপনার ডেমো OTP কোড: 582910", show_alert=True)

    elif data == "search_num":
        context.user_data['state'] = "waiting_for_search_range"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(
            "🔍 **নাম্বার রেঞ্জ সার্চ:**\n\nদয়া করে আপনি যে রেঞ্জের নাম্বার চাচ্ছেন তা লিখে পাঠান (যেমন: `+88017`):",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="Markdown"
        )

    elif data == "live_traffic":
        await query.answer("🚦 Live Traffic: সকল সার্ভার বর্তমানে চালু আছে!", show_alert=True)

    elif data == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        msg = (
            f"👥 **রেফার এন্ড আর্ন প্রোগ্রাম**\n\n"
            f"আপনার বন্ধুকে ইনভাইট করুন এবং আকর্ষণীয় বোনাস জিতুন!\n\n"
            f"📌 **আপনার রেফারেল লিংক:**\n`{ref_link}`\n\n"
            f"📜 **রেফারেল নিয়মাবলী:**\n"
            f"• প্রতি সফল রেফারে পাবেন: **৳{REFERRAL_BONUS:.2f}**\n"
            f"• যাকে রেফার করবেন তাকে অন্তত **{MIN_REFERRED_OTPS}টি ওটিপি** রিসিভ করতে হবে।\n"
            f"• টাকা উইথড্র করতে সর্বনিম্ন **{MIN_VALID_REFERS}টি সফল রেফার** লাগবে।\n\n"
            f"📊 **আপনার স্ট্যাটাস:**\n"
            f"• মোট সফল রেফার: **{user_wallet['valid_refers']} জন**"
        )
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "wallet":
        msg = (
            f"👛 **আপনার ওয়ালেট বিবরণী:**\n\n"
            f"💰 মোট জমানো টাকা: **৳{user_wallet['balance']:.2f}**\n"
            f"📥 আপনার মোট সফল ওটিপি: **{user_wallet['success_otps']} টি**\n"
            f"👥 আপনার সফল রেফারেল: **{user_wallet['valid_refers']} / {MIN_VALID_REFERS} জন**\n\n"
            f"📌 **উইথড্রল শর্তাবলী:**\n"
            f"• মিনিমাম ব্যালেন্স: **৳{MIN_WITHDRAW:.2f}**\n"
            f"• মিনিমাম রেফারেল: **{MIN_VALID_REFERS} জন** (যাদের ৫০টি করে ওটিপি থাকতে হবে)\n\n"
            f"টাকা তুলতে নিচের মাধ্যম বেছে নিন:"
        )
        btn = [
            [InlineKeyboardButton("💖 বিকাশ (bKash)", callback_data="withdraw_bKash"), InlineKeyboardButton("🟠 নগদ (Nagad)", callback_data="withdraw_Nagad")],
            [InlineKeyboardButton("💜 রকেট (Rocket)", callback_data="withdraw_Rocket"), InlineKeyboardButton("🟡 বাইনান্স (Binance)", callback_data="withdraw_Binance")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data.startswith("withdraw_"):
        method = data.replace("withdraw_", "")
        
        if user_wallet['balance'] < MIN_WITHDRAW:
            await query.answer(f"❌ উইথড্র করতে ওয়ালেটে সর্বনিম্ন ৳{MIN_WITHDRAW:.2f} থাকতে হবে!", show_alert=True)
            return

        if user_wallet['valid_refers'] < MIN_VALID_REFERS:
            await query.answer(
                f"❌ উইথড্র করতে আপনার অন্তত {MIN_VALID_REFERS}টি সফল রেফার দরকার!\n"
                f"আপনার বর্তমান সফল রেফার: {user_wallet['valid_refers']} জন।", 
                show_alert=True
            )
            return

        context.user_data['state'] = "waiting_for_withdraw_acc"
        context.user_data['withdraw_method'] = method

        if method in ["bKash", "Nagad", "Rocket"]:
            prompt = f"📱 **{method} উইথড্রল:**\n\nদয়া করে আপনার **{method} নাম্বারটি** লিখে পাঠান:"
        else:
            prompt = f"🟡 **Binance উইথড্রল:**\n\nদয়া করে আপনার **Binance Pay ID / BEP20 Address** টি লিখে পাঠান:"

        btn = [[InlineKeyboardButton("🔙 Cancel", callback_data="wallet")]]
        await query.edit_message_text(prompt, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "2fa_menu":
        context.user_data['state'] = "waiting_for_2fa"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(
            "🔐 **2FA Code Generator (Facebook / Instagram)**\n\n"
            "দয়া করে আপনার টু-এফএ সিক্রেট কি (Secret Key) লিখে পাঠান:",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="Markdown"
        )

    elif data == "support":
        support_msg = f"💬 **অনলাইন সাপোর্ট:**\n\nযে কোনো সমস্যায় সরাসরি অ্যাডমিনের সাথে যোগাযোগ করুন:\n👉 Telegram: [@{ADMIN_USERNAME}](https://t.me/{ADMIN_USERNAME})"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(support_msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.answer("❌ আপনি এই বটের এডমিন নন!", show_alert=True)
            return
        
        admin_btns = [
            [InlineKeyboardButton("💳 Check Panel Balance", callback_data="admin_balance")],
            [InlineKeyboardButton("👥 User Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 Broadcast Notification", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        await query.edit_message_text("⚙️ **Welcome to Owner Admin Dashboard**", reply_markup=InlineKeyboardMarkup(admin_btns), parse_mode="Markdown")

    elif data == "admin_balance":
        if user_id != ADMIN_ID: return
        back_btn = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text("💰 **প্যানেল ব্যালেন্স:** $50.00 (ডেমো)", reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="Markdown")

    elif data == "admin_stats":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()
        
        back_btn = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(f"📊 **ইউজার স্ট্যাটিস্টিক্স:**\n\n• মোট রেজিস্টার্ড ইউজার: {total_users} জন", reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="Markdown")

    elif data == "admin_broadcast":
        if user_id != ADMIN_ID: return
        back_btn = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text("📢 **ব্রডকাস্ট সিস্টেম:** এপিআই সংযোগের পর চালু হবে।", reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="Markdown")

    elif data == "back_main":
        context.user_data.clear()
        await show_main_menu(query, context, is_edit=True)

# টেক্সট মেসেজ ও কিবোর্ডের বাটন প্রেস হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    user_id = update.effective_user.id
    user_wallet = get_user_data(user_id)
    state = context.user_data.get('state')

    if user_text == "📞 Get Number":
        services = [
            [InlineKeyboardButton("📘 Facebook", callback_data="buy_fb"), InlineKeyboardButton("🟢 WhatsApp", callback_data="buy_wa")],
            [InlineKeyboardButton("✈️ Telegram", callback_data="buy_tg"), InlineKeyboardButton("🟡 IMO", callback_data="buy_imo")],
            [InlineKeyboardButton("📸 Instagram", callback_data="buy_insta")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]
        ]
        await update.message.reply_text("📱 **যে সার্ভিসের নাম্বার দরকার বেছে নিন:**", reply_markup=InlineKeyboardMarkup(services), parse_mode="Markdown")
        return

    elif user_text == "👛 Wallet":
        msg = (
            f"👛 **আপনার ওয়ালেট বিবরণী:**\n\n"
            f"💰 মোট জমানো টাকা: **৳{user_wallet['balance']:.2f}**\n"
            f"📥 আপনার মোট সফল ওটিপি: **{user_wallet['success_otps']} টি**\n"
            f"👥 আপনার সফল রেফারেল: **{user_wallet['valid_refers']} / {MIN_VALID_REFERS} জন**\n\n"
            f"📌 **উইথড্রল শর্তাবলী:**\n"
            f"• মিনিমাম ব্যালেন্স: **৳{MIN_WITHDRAW:.2f}**\n"
            f"• মিনিমাম রেফারেল: **{MIN_VALID_REFERS} জন** (যাদের ৫০টি করে ওটিপি থাকতে হবে)"
        )
        btn = [
            [InlineKeyboardButton("💖 বিকাশ (bKash)", callback_data="withdraw_bKash"), InlineKeyboardButton("🟠 নগদ (Nagad)", callback_data="withdraw_Nagad")],
            [InlineKeyboardButton("💜 রকেট (Rocket)", callback_data="withdraw_Rocket"), InlineKeyboardButton("🟡 বাইনান্স (Binance)", callback_data="withdraw_Binance")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        return

    elif user_text == "👥 Invite Friends":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        msg = (
 
