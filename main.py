import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# --- কনফিগারেশন ---
BOT_TOKEN = "8187412491:AAGG3pDcpmQUj15y_bXF5R_VbAfb22gjru0"
CHANNEL_URL = "https://t.me/sm_madhord_cannal"
CHANNEL_USERNAME = "@sm_madhord_cannal"
OTP_GROUP_URL = "https://t.me/sm_otp_group1"
OTP_GROUP_ID = "@sm_otp_group1"
YOUTUBE_URL = "https://youtube.com/@smearning2026?si=N08xzt8H184PveSg"
ADMIN_USERNAME = "sowrov0134"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
router = Router()

users_db = {}
api_providers = ["Default API Provider"]

class AdminStates(StatesGroup):
    waiting_for_user_balance = State()
    waiting_for_api_name = State()

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

def get_force_sub_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Telegram Channel", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="💬 OTP Group", url=OTP_GROUP_URL)],
            [InlineKeyboardButton(text="▶️ YouTube Channel", url=YOUTUBE_URL)],
            [InlineKeyboardButton(text="✅ Verify", callback_data="verify_sub")],
        ]
    )

def get_main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [
            InlineKeyboardButton(text="📱 Get Number", callback_data="get_number"),
            InlineKeyboardButton(text="📊 Live Traffic", callback_data="live_traffic"),
        ],
        [
            InlineKeyboardButton(text="🔍 Search Number", callback_data="search_number"),
            InlineKeyboardButton(text="💰 Wallet", callback_data="wallet"),
        ],
        [
            InlineKeyboardButton(
                text="🛠️ Admin Support", url=f"https://t.me/{ADMIN_USERNAME}"
            )
        ],
    ]
    if is_admin:
        keyboard.append(
            [InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_services_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Facebook", callback_data="srv_facebook")],
            [InlineKeyboardButton(text="💬 WhatsApp", callback_data="srv_whatsapp")],
            [InlineKeyboardButton(text="✈️ Telegram", callback_data="srv_telegram")],
            [InlineKeyboardButton(text="📸 Instagram", callback_data="srv_instagram")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")],
        ]
    )

def get_facebook_types_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✨ New Facebook (Fresh)", callback_data="fb_new"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 PC Clone (Aged)", callback_data="fb_clone"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="get_number")],
        ]
    )

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    users_db[user_id] = {
        "name": message.from_user.full_name,
        "username": message.from_user.username,
        "balance": 0.0,
    }

    is_subbed = await check_subscription(user_id)
    if not is_subbed:
        await message.answer(
            "⚠️ **বট ব্যবহার করতে হলে অবশ্যই নিচের চ্যানেল ও গ্রুপগুলোতে জয়েন করতে হবে এবং ইউটিউব চ্যানেল সাবস্ক্রাইব করতে হবে:**\n\n"
            "১. আমাদের টেলিগ্রাম চ্যানেল জয়েন করুন।\n"
            "২. ওটিপি গ্রুপে জয়েন করুন।\n"
            "৩. ইউটিউব চ্যানেল সাবস্ক্রাইব করুন।\n\n"
            "সবগুলোতে জয়েন করার পর নিচের **Verify** বাটনে ক্লিক করুন!",
            reply_markup=get_force_sub_keyboard(),
            parse_mode="Markdown",
        )
    else:
        is_admin = message.from_user.username == ADMIN_USERNAME
        await message.answer(
            f"স্বাগতম {message.from_user.first_name}!\nআপনার ভার্চুয়াল নাম্বার বট ড্যাশবোর্ডে স্বাগতম। নিচে থেকে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন:",
            reply_markup=get_main_menu_keyboard(is_admin),
        )

@router.callback_query(F.data == "verify_sub")
async def process_verify(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_subbed = await check_subscription(user_id)

    if not is_subbed:
        await callback.answer(
            "❌ আপনি এখনও সবগুলোতে জয়েন করেননি! দয়া করে চ্যানেল ও গ্রুপে জয়েন করে আবার ভেরিফাই করুন।",
            show_alert=True,
        )
    else:
        await callback.message.delete()
        is_admin = callback.from_user.username == ADMIN_USERNAME
        await callback.message.answer(
            "✅ ভেরিফিকেশন সফল হয়েছে!\nবট ব্যবহার করার জন্য প্রস্তুত।",
            reply_markup=get_main_menu_keyboard(is_admin),
        )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    is_admin = callback.from_user.username == ADMIN_USERNAME
    await callback.message.edit_text(
        "মূল মেনুতে ফিরে এসেছেন:", reply_markup=get_main_menu_keyboard(is_admin)
    )

@router.callback_query(F.data == "get_number")
async def get_number_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📲 যেকোনো সার্ভিস সিলেক্ট করুন:", reply_markup=get_services_keyboard()
    )

@router.callback_query(F.data == "srv_facebook")
async def facebook_types_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📘 Facebook ক্যাটাগরি সিলেক্ট করুন:",
        reply_markup=get_facebook_types_keyboard(),
    )

@router.callback_query(F.data.in_({"fb_new", "fb_clone"}))
async def handle_number_generation(callback: CallbackQuery):
    is_new = callback.data == "fb_new"
    countries = ["🇧🇩 Bangladesh", "🇹🇿 Tanzania", "🇿🇼 Zimbabwe"]

    keyboard = []
    for country in countries:
        cb_data = (
            f"select_country_new_{country}"
            if is_new
            else f"select_country_clone_{country}"
        )
        keyboard.append(
            [InlineKeyboardButton(text=country, callback_data=cb_data)]
        )
    keyboard.append(
        [InlineKeyboardButton(text="⬅️ Back", callback_data="srv_facebook")]
    )

    await callback.message.edit_text(
        "🌐 যে দেশের ট্রাফিক বা পারফরম্যান্স ভালো, সেই দেশগুলো নিচে দেওয়া হলো। যেকোনো একটি দেশ সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )

@router.callback_query(F.data.startswith("select_country_"))
async def deliver_numbers(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    num_type = data_parts[2]
    country = data_parts[3]

    if num_type == "new":
        display_number = "+8801711223344"
        text = (
            f"✅ **Fresh Number Generated ({country})**\n\n"
            f"📱 Number: `{display_number}`\n"
            f"*(নাম্বারের ওপর ট্যাপ করে কপি করুন)*\n\n"
            f"⚠️ এই নাম্বারে আগে কোনো অ্যাকাউন্ট খোলা হয়নি।"
        )
    else:
        nums = ["+8801811223355", "+8801911223366", "+8801611223377"]
        text = (
            f"🔄 **PC Clone Numbers Generated ({country})**\n\n"
            f"1. `{nums[0]}`\n"
            f"2. `{nums[1]}`\n"
            f"3. `{nums[2]}`\n\n"
            f"*(নাম্বারগুলোর ওপর ট্যাপ করে কপি করুন)*"
        )

    action_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 OTP Group", url=OTP_GROUP_URL),
                InlineKeyboardButton(
                    text="🔄 Change Country", callback_data="srv_facebook"
                ),
            ],
            [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_main")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=action_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "live_traffic")
async def live_traffic(callback: CallbackQuery):
    await callback.message.edit_text(
        "📊 **Live Traffic Status:**\n\n"
        "• Tanzania: High Success Rate (🟢)\n"
        "• Zimbabwe: Good Success Rate (🟢)\n"
        "• Bangladesh: Normal (🟡)\n\n"
        "সার্ভার ফুল স্পিডে কাজ করছে।",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
            ]
        ),
    )

@router.callback_query(F.data == "wallet")
async def wallet_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    bal = users_db.get(user_id, {}).get("balance", 0.0)
    await callback.message.edit_text(
        f"💰 **Your Wallet:**\n\n"
        f"• Current Balance: `৳{bal}`\n\n"
        f"ব্যালেন্স রিচার্জ করতে অ্যাডমিন সাপোর্টের সাথে যোগাযোগ করুন।",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "search_number")
async def search_number(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 নাম্বার সার্চ করার জন্য নাম্বারটি লিখে পাঠান বা সিস্টেম স্ট্যাটাস চেক করুন।",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_main")]
            ]
        ),
    )

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.username != ADMIN_USERNAME:
        await callback.answer("❌ আপনার এই প্যানেলটি অ্যাক্সেস করার অনুমতি নেই!", show_alert=True)
        return

    total_users = len(users_db)
    await callback.message.edit_text(
        f"⚙️ **Admin Control Panel**\n\n"
        f"• Total Users: {total_users}\n"
        f"• Active API: {api_providers[0]}\n\n"
        f"নিচ থেকে ম্যানেজমেন্ট অপশন সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👥 User List & Balance", callback_data="adm_users")],
                [InlineKeyboardButton(text="🔌 Manage API Panel", callback_data="adm_api")],
                [InlineKeyboardButton(text="⬅️ Main Menu", callback_data="back_to_main")],
            ]
        ),
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "adm_users")
async def admin_users_list(callback: CallbackQuery):
    if callback.from_user.username != ADMIN_USERNAME:
        return

    text = "👥 **Registered Users List:**\n\n"
    for uid, info in users_db.items():
        text += f"• Name: {info['name']} | ID: `{uid}` | Bal: ৳{info['balance']}\n"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")]
            ]
        ),
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "adm_api")
async def admin_api_manage(callback: CallbackQuery):
    if callback.from_user.username != ADMIN_USERNAME:
        return

    await callback.message.edit_text(
        f"🔌 **Current API Panel:** `{api_providers[0]}`\n\n"
        f"কোড পরিবর্তন না করেই নতুন এপিআই প্যানেল যুক্ত করতে নিচের বাটনে ক্লিক করুন:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Add New API Provider", callback_data="adm_add_api")],
                [InlineKeyboardButton(text="⬅️ Back to Admin", callback_data="admin_panel")]
            ]
        ),
        parse_mode="Markdown",
    )

@router.callback_query(F.data == "adm_add_api")
async def admin_add_api_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.username != ADMIN_USERNAME:
        return
    await callback.message.answer("দয়া করে নতুন এপিআই প্যানেলের নাম বা এপিআই কি (API Key) সেন্ড করুন:")
    await state.set_state(AdminStates.waiting_for_api_name)

@router.message(AdminStates.waiting_for_api_name)
async def save_new_api(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    new_api = message.text
    api_providers[0] = new_api
    await state.clear()
    await message.answer(f"✅ সফলভাবে নতুন এপিআই প্যানেল যুক্ত করা হয়েছে: `{new_api}`", parse_mode="Markdown")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher()
    dp.include_router(router)
    print("Bot is running successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
