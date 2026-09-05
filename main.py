        except ValueError:
            pass

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

# বাটন হ্যান্ডলার
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_wallet = get_user_data(user_id)

    if data == "check_join":
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
                
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 **অভিনন্দন!** আপনার রেফার করা ইউজার (`{user_id}`) ৫০টি ওটিপি সম্পন্ন করেছে।\n\n"
                             f"💰 আপনার ওয়ালেটে **৳{REFERRAL_BONUS:.2f}** যোগ হয়েছে!",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass

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
        total_users = len(USER_WALLETS)
        back_btn = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text(f"📊 **ইউজার স্ট্যাটিস্টিক্স:**\n\n• মোট রেজিস্টার্ড ইউজার: {total_users} জন", reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="Markdown")

    elif data == "admin_broadcast":
        if user_id != ADMIN_ID: return
        back_btn = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        await query.edit_message_text("📢 **ব্রডকাস্ট সিস্টেম:** এপিআই সংযোগের পর চালু হবে।", reply_markup=InlineKeyboardMarkup(back_btn), parse_mode="Markdown")

    elif data == "back_main":
        context.user_data.clear()
        await show_main_menu(query, context, is_edit=True)

# মেসেজ হ্যান্ডলার
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    user_id = update.effective_user.id
    user_wallet = get_user_data(user_id)
    state = context.user_data.get('state')

    if state == "waiting_for_2fa":
        current_code = generate_totp(user_text)
        if current_code:
            await update.message.reply_text(f"✅ **আপনার 2FA কোড:** `{current_code}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ ইনভ্যালিড 2FA কী!")
        context.user_data['state'] = None
        return

    elif state == "waiting_for_search_range":
        await update.message.reply_text(f"🔍 **{user_text}** রেঞ্জের জন্য নাম্বার খোঁজা হচ্ছে...")
        context.user_data['state'] = None
        return

    elif state == "waiting_for_withdraw_acc":
        context.user_data['withdraw_acc'] = user_text
        context.user_data['state'] = "waiting_for_withdraw_amount"
        await update.message.reply_text(
            f"✅ **পেমেন্ট অ্যাড্রেস রিসিভ হয়েছে!**\n\n"
            f"💰 ওয়ালেট ব্যালেন্স: **৳{user_wallet['balance']:.2f}**\n"
            f"এখন আপনি কত টাকা উইথড্র করতে চান তা লিখে পাঠান:",
            parse_mode="Markdown"
        )
        return

    elif state == "waiting_for_withdraw_amount":
        try:
            amount = float(user_text)
            if amount < MIN_WITHDRAW:
                await update.message.reply_text(f"❌ সর্বনিম্ন উইথড্র পরিমাণ **৳{MIN_WITHDRAW:.2f}**!")
                return
            if amount > user_wallet['balance']:
                await update.message.reply_text(f"❌ পর্যাপ্ত ব্যালেন্স নেই!")
                return
            
            method = context.user_data.get('withdraw_method')
            acc = context.user_data.get('withdraw_acc')
            
            user_wallet['balance'] -= amount
            await update.message.reply_text("🎉 **উইথড্র রিকোয়েস্ট সফল হয়েছে!**", parse_mode="Markdown")
            
            admin_msg = f"🔔 **নতুন উইথড্র!**\n\n👤 ইউজার: `{user_id}`\n💳 মেথড: {method}\n📌 অ্যাকাউন্ট: `{acc}`\n💰 পরিমাণ: ৳{amount:.2f}"
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
            except Exception:
                pass

        except ValueError:
            await update.message.reply_text("❌ দয়া করে সংখ্যা লিখে পাঠান!")
            return

        context.user_data.clear()
        return

# থ্রি-ডট বোতাম সেটআপ
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start", "🚀 Start / Restart Bot")
    ])

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running perfectly now...")
    app.run_polling()
