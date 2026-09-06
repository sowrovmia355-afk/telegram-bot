from flask import Flask
from threading import Thread
import sqlite3

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

import logging
import base64
import hmac
import hashlib
import struct
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8610842156:AAF03CmhwZX4h16lDx_zODCLRuH_iCexf7o"
ADMIN_ID = 8791376128
ADMIN_USERNAME = "sowrov0134"

TELEGRAM_CHANNEL = "https://t.me/smearnin013"
OTP_BOT_LINK = "https://t.me/sowrov536"
YOUTUBE_LINK = "https://youtube.com/@smearning2026"

OTP_RATE = 0.20
REFERRAL_BONUS = 10.0
MIN_WITHDRAW = 120.0
MIN_REFERRED_OTPS = 50
MIN_VALID_REFERS = 3

DB_FILE = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, success_otps INTEGER DEFAULT 0, referred_by INTEGER DEFAULT NULL, valid_refers INTEGER DEFAULT 0, claimed_refers TEXT DEFAULT "")''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS verified (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, success_otps, referred_by, valid_refers, claimed_refers FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance, success_otps, referred_by, valid_refers, claimed_refers) VALUES (?, 0.0, 0, NULL, 0, '')", (user_id,))
        conn.commit()
        data = {"balance": 0.0, "success_otps": 0, "referred_by": None, "valid_refers": 0, "claimed_refers": set()}
    else:
        claimed = [int(x) for x in row[4].split(",") if x.strip()]
        data = {"balance": row[0], "success_otps": row[1], "referred_by": row[2], "valid_refers": row[3], "claimed_refers": set(claimed)}
    conn.close()
    return data

def save_user_data(user_id, data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    claimed_str = ",".join([str(x) for x in data["claimed_refers"]])
    cursor.execute("UPDATE users SET balance = ?, success_otps = ?, referred_by = ?, valid_refers = ?, claimed_refers = ? WHERE user_id = ?", (data["balance"], data["success_otps"], data["referred_by"], data["valid_refers"], claimed_str, user_id))
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
        import time
        counter = int(time.time() // 30)
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        o = digest[19] & 15
        code = (struct.unpack(">I", digest[o:o+4])[0] & 0x7fffffff) % 1000000
        return f"{code:06d}"
    except Exception:
        return None

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

    text = "👋 আমাদের নাম্বার বটে স্বাগতম!\n\nনিচের মেনু বা কিবোর্ড থেকে আপনার প্রয়োজনীয় সার্ভিসটি বেছে নিন:"
    reply_kb = get_reply_keyboard(user_id)

    if is_edit and hasattr(update_or_query, 'edit_message_text'):
        try:
            await update_or_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
            return
        except Exception:
            pass
    
    target = update_or_query.message if hasattr(update_or_query, 'message') and update_or_query.message else update_or_query
    await target.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await target.reply_text("👇 নিচ থেকেও শর্টকাট মেনু ব্যবহার করতে পারেন:", reply_markup=reply_kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
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
        await show_main_menu(update, context, is_edit=False)
        return

    buttons = [
        [InlineKeyboardButton("📢 Telegram Channel", url=TELEGRAM_CHANNEL)],
        [InlineKeyboardButton("🤖 Telegram OTP Channel", url=OTP_BOT_LINK)],
        [InlineKeyboardButton("▶️ Subscribe YouTube", url=YOUTUBE_LINK)],
        [InlineKeyboardButton("✅ Joined / Verify", callback_data="check_join")]
    ]
    await update.message.reply_text("⚠️ বটটি ব্যবহার করতে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে!\n\nজয়েন শেষ হলে Verify বাটনে চাপ দিন।", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    wallet = get_user_data(user_id)

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
        await query.edit_message_text("📱 যে সার্ভিসের নাম্বার দরকার বেছে নিন:", reply_markup=InlineKeyboardMarkup(services))

    elif data.startswith("buy_"):
        service_name = data.replace("buy_", "").upper()
        demo_number = "+8801700000000"
        
        wallet["success_otps"] += 1
        wallet["balance"] += OTP_RATE

        ref_id = wallet.get("referred_by")
        if ref_id and wallet["success_otps"] >= MIN_REFERRED_OTPS:
            ref_wallet = get_user_data(ref_id)
            if user_id not in ref_wallet["claimed_refers"]:
                ref_wallet["claimed_refers"].add(user_id)
                ref_wallet["valid_refers"] += 1
                ref_wallet["balance"] += REFERRAL_BONUS
                save_user_data(ref_id, ref_wallet)
                try:
                    await context.bot.send_message(chat_id=ref_id, text=f"🎉 অভিনন্দন! আপনার রেফার করা ইউজার ৫০টি ওটিপি সম্পন্ন করেছে। আপনার ওয়ালেটে ৳{REFERRAL_BONUS} যোগ হয়েছে!")
                except Exception:
                    pass
        
        save_user_data(user_id, wallet)
        msg = f"✅ আপনার {service_name} নাম্বার রেডি!\n\n📞 নাম্বার: `{demo_number}`\n\nকোড চেক করতে নিচের বাটনে চাপ দিন।"
        btn = [
            [InlineKeyboardButton("📩 Check OTP", callback_data="demo_otp")],
            [InlineKeyboardButton("🔙 Back", callback_data="get_number")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "demo_otp":
        await query.answer("📩 আপনার ডেমো OTP কোড: 582910", show_alert=True)

    elif data == "search_num":
        context.user_data['state'] = "waiting_for_search_range"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text("🔍 নাম্বার রেঞ্জ লিখে পাঠান (যেমন: +88017):", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "live_traffic":
        await query.answer("🚦 Live Traffic: সকল সার্ভার চালু আছে!", show_alert=True)

    elif data == "refer":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        msg = f"👥 রেফার এন্ড আর্ন প্রোগ্রাম\n\nলিংক:\n`{ref_link}`\n\n• প্রতি রেফার: ৳{REFERRAL_BONUS}\n• সফল রেফার: {wallet['valid_refers']} জন"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "wallet":
        msg = f"👛 ওয়ালেট বিবরণী:\n\n💰 ব্যালেন্স: ৳{wallet['balance']:.2f}\n📥 সফল ওটিপি: {wallet['success_otps']}\n👥 রেফার: {wallet['valid_refers']} / {MIN_VALID_REFERS}"
        btn = [
            [InlineKeyboardButton("💖 বিকাশ", callback_data="withdraw_bKash"), InlineKeyboardButton("🟠 নগদ", callback_data="withdraw_Nagad")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif data.startswith("withdraw_"):
        method = data.replace("withdraw_", "")
        if wallet['balance'] < MIN_WITHDRAW:
            await query.answer(f"❌ সর্বনিম্ন উইথড্র ৳{MIN_WITHDRAW}!", show_alert=True)
            return
        context.user_data['state'] = "waiting_for_withdraw_acc"
        context.user_data['withdraw_method'] = method
        btn = [[InlineKeyboardButton("🔙 Cancel", callback_data="wallet")]]
        await query.edit_message_text(f"📱 আপনার {method} নাম্বারটি লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "2fa_menu":
        context.user_data['state'] = "waiting_for_2fa"
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text("🔐 আপনার 2FA সিক্রেট কি লিখে পাঠান:", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "support":
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(f"💬 সাপোর্ট: @{ADMIN_USERNAME}", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.answer("❌ আপনি এডমিন নন!", show_alert=True)
            return
        admin_btns = [
            [InlineKeyboardButton("👥 User Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ]
        await query.edit_message_text("⚙️ Admin Dashboard", reply_markup=InlineKeyboardMarkup(admin_btns))

    elif data == "admin_stats":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        conn.close()
        btn = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        await query.edit_message_text(f"📊 মোট ইউজার: {total} জন", reply_markup=InlineKeyboardMarkup(btn))

    elif data == "back_main":
        context.user_data.clear()
        await show_main_menu(query, context, is_edit=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    wallet = get_user_data(user_id)
    state = context.user_data.get('state')

    if text == "📞 Get Number":
        services = [
            [InlineKeyboardButton("📘 Facebook", callback_data="buy_fb"), InlineKeyboardButton("🟢 WhatsApp", callback_data="buy_wa")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]
        ]
        await update.message.reply_text("📱 সার্ভিস বেছে নিন:", reply_markup=InlineKeyboardMarkup(services))
        return
    elif text == "👛 Wallet":
        await update.message.reply_text(f"💰 ব্যালেন্স: ৳{wallet['balance']:.2f}\n📥 ওটিপি: {wallet['success_otps']}")
        return
    elif text == "👥 Invite Friends":
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(f"লিংক: `{ref_link}`", parse_mode="Markdown")
        return
    elif text == "🚦 Live Traffic":
        await update.message.reply_text("🚦 সকল সার্ভার চালু আছে!")
        return
    elif text == "🔐 Facebook 2FA":
        context.user_data['state'] = "waiting_for_2fa"
        await update.message.reply_text("🔐 2FA সিক্রেট কি পাঠান:")
        return
    elif text == "💬 Online Support":
        await update.message.reply_text(f"সাপোর্ট: @{ADMIN_USERNAME}")
        return

    if state == "waiting_for_2fa":
        code = generate_totp(text)
        if code:
            await update.message.reply_text(f"✅ কোড: `{code}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ ভুল কী!")
        context.user_data['state'] = None
    elif state == "waiting_for_search_range":
        await update.message.reply_text(f"🔍 খোঁজ করা হচ্ছে: {text}")
        context.user_data['state'] = None
    elif state == "waiting_for_withdraw_acc":
        context.user_data['withdraw_acc'] = text
        context.user_data['state'] = "waiting_for_withdraw_amount"
        await update.message.reply_text("💰 কত টাকা উইথড্র করতে চান লিখে পাঠান:")
    elif state == "waiting_for_withdraw_amount":
        try:
            amt = float(text)
            if amt < MIN_WITHDRAW or amt > wallet['balance']:
                await update.message.reply_text("❌ পর্যাপ্ত ব্যালেন্স নেই বা মিনিমাম অ্যামাউন্ট হয়নি!")
                return
            wallet['balance'] -= amt
            save_user_data(user_id, wallet)
            await update.message.reply_text("🎉 উইথড্র রিকোয়েস্ট সফল হয়েছে!")
        except ValueError:
            await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন!")
        context.user_data.clear()

async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Start Bot"),
        BotCommand("wallet", "Wallet"),
        BotCommand("refer", "Referral"),
        BotCommand("support", "Support")
    ])

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
