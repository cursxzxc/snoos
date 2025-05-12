from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(user_name):
    welcome_text = (
        f"<b>Приветствуем вас, {user_name}!</b>\n\n"
        "<blockquote>"
        "Этот Telegram-бот создан как многофункциональный инструмент. "
        "Он поможет вам с восстановлением аккаунтов и другими полезными задачами."
        "</blockquote>"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Раздел задач", callback_data="tasks")],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="📩 Поддержка", callback_data="support")
        ]
    ])
    return welcome_text, keyboard

def get_profile_menu(username, user_id, balance, subscription, sub_end_date):
    subscription_status = "Присутствует" if subscription else "Отсутствует"
    sub_date = sub_end_date if sub_end_date else "—"
    
    profile_text = (
        "<b>👤 Ваш профиль</b>\n\n"
        "<i>Информация о вас</i>\n"
        "<blockquote>"
        f"☃ <b>Юзернейм:</b> @{username}\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"💰 <b>Баланс:</b> {balance}"
        "</blockquote>\n\n"
        f"🎟 <b>Подписка:</b> {subscription_status}\n"
        f"⏳ <b>Действует до:</b> {sub_date}"
    )
    
    profile_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Пополнить", callback_data="subscribe"),
            InlineKeyboardButton(text="🎟 Управление подпиской", callback_data="manage_sub")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ])
    
    return profile_text, profile_keyboard
