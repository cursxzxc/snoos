import asyncio
import sqlite3
import os
import random
import aiohttp
import json
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from aiocryptopay import AioCryptoPay, Networks
from colorama import Fore, Style
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from menu import get_main_menu, get_profile_menu
import logging

# Токены и настройки
TOKEN = "7910780285:AAEqqgUEVp4-OCjRtPlMoyglahXAfvmS-jA"
CRYPTO_TOKEN = "375504:AA7rjWCn9vTcYdDHtt4R6AmcgSGdESe5bMZ"
ADMIN_ID = 8142435328
API_ID = 26797823
API_HASH = "1553515f0a80666f58dc09fdf86ddd22"
SESSIONS_PATH = "app"  # нечего не меняй так и должно быть

bot = Bot(token=TOKEN)
dp = Dispatcher()
crypto = AioCryptoPay(token=CRYPTO_TOKEN)

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "database.db")
PHOTO_PATH = "images/profile.png"
REPORT_PATH = "report.json"
BOT_ENABLED = True

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def load_recovery_texts():
    if not os.path.exists(REPORT_PATH):
        RECOVERY_TEXTS = [
            {
                "text": "Пожалуйста, восстановите мой {number}, его забанили из-за фейковых жалоб!"
            },
            {"text": "Срочно нужен мой {number}, хейтеры накидали фальшивых репортов!"},
            {"text": "Мій {number} заблоковано через спам скарг, поверніть доступ!"},
            {"text": "Мой {number} в бане, какие-то недоброжелатели пожаловались!"},
            {"text": "Мій {number} відключено через наклепи, я нічого не порушував!"},
            {"text": "Система ошиблась! Мой {number} в бане из-за ложных жалоб!"},
            {"text": "Вы серьёзно? {number} заблокирован из-за необоснованных жалоб!"},
            {
                "text": "Мой {number} забанен без причины! Кто-то решил испортить мне жизнь!"
            },
            {"text": "Сталася біда! {number} відключено через фейкові скарги!"},
            {"text": "Почему мой {number} в бане? Какие-то люди отправили жалобы!"},
            {"text": "Telegram – моє життя, а ви забанили мій {number}!"},
            {
                "text": "Без причин блокировать аккаунт несправедливо! Разбаньте мой {number}!"
            },
            {"text": "Как мне теперь общаться? {number} заблокирован из-за хейтеров!"},
            {"text": "Не розумію, що сталося! {number} забанено без причин!"},
            {"text": "Мой {number} снова в бане из-за наспамленных жалоб!"},
            {"text": "Прошу розібратися! Мій {number} відключено через помилку!"},
            {"text": "Я всегда соблюдал правила! Почему мой {number} забанен?"},
            {"text": "Розбаньте мій {number}, я чесно використовував Telegram!"},
        ]
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(RECOVERY_TEXTS, f, ensure_ascii=False, indent=4)
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


RECOVERY_TEXTS = load_recovery_texts()

REPORT_MESSAGES = [
    "Этот пользователь постоянно спамит, пожалуйста, заблокируйте его!",
    "Спам от этого человека уже невыносим, примите меры!",
    "Каждый день одно и то же — спам, уберите его из чата!",
    "Обратите внимание, этот аккаунт засыпает чат спамом.",
    "Серьёзно, сколько можно терпеть этот спам? Забаньте его!",
    "Этот спамер мешает всем, пора его остановить.",
    "Прошу заблокировать, спам от него достал!",
    "Админы, тут один тип спамит без конца, сделайте что-то!",
    "Спам от этого юзера портит чат, удалите его.",
    "Снова спамит, прошу забанить этого пользователя!",
    "Избавьте нас от этого спамера, пожалуйста!",
    "Тут один постоянно спамит, можно его убрать?",
    "Спам каждый день, сил нет, заблокируйте его!",
    "Посмотрите, этот аккаунт опять спамит, пора действовать.",
    "Давайте забаним его, спамит без остановки!",
    "Обратите внимание, тут спамят постоянно.",
    "Он опять спамит, жалобы летят, забаньте!",
    "Спам мешает общению, уберите этого пользователя!",
    "Этот спамер уже всех достал, пора его выгнать.",
    "Тут один юзер спамит, прошу его заблокировать!",
    "Спамит так, что читать невозможно, примите меры!",
    "Реально надоел этот спам, давайте его в бан!",
    "Прошу остановить этого спамера, мешает чату.",
    "Третий раз вижу спам от него, забаньте уже!",
    "Спам раздражает, можно его убрать из чата?",
    "Админы, тут спамят, пора что-то сделать!",
    "Он спамит снова и снова, выгоните его!",
    "Заблокируйте этого спамера, мешает общаться!",
    "Спам без перерыва, прошу его забанить.",
    "Этот пользователь спамит, уберите его, пожалуйста!",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Mobile Safari/537.36",
]


class RecoveryStates(StatesGroup):
    waiting_for_phone = State()


class SnosingStates(StatesGroup):
    waiting_for_link = State()


def init_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """CREATE TABLE IF NOT EXISTS users 
                (user_id INTEGER PRIMARY KEY, 
                 balance REAL DEFAULT 0.0,
                 subscription INTEGER DEFAULT 0,
                 sub_end_date TEXT,
                 next_snuser_usage TEXT)"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS payments 
                (check_id TEXT PRIMARY KEY,
                 user_id INTEGER,
                 amount REAL,
                 days INTEGER,
                 status TEXT,
                 created_at TEXT)"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS recovery_requests 
                (user_id INTEGER,
                 phone_number TEXT,
                 status TEXT,
                 created_at TEXT)"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS bot_settings 
                (setting_key TEXT PRIMARY KEY,
                 setting_value TEXT)"""
    )
    conn.commit()
    conn.close()


def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT balance, subscription, sub_end_date, next_snuser_usage FROM users WHERE user_id = ?",
        (user_id,),
    )
    result = c.fetchone()
    if result is None:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        result = (0.0, 0, None, None)
    conn.close()
    return result


def set_subscription(user_id, days):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT subscription, sub_end_date FROM users WHERE user_id = ?", (user_id,)
    )
    current = c.fetchone()
    if current and current[0] == 1 and current[1]:
        try:
            current_end_date = datetime.strptime(current[1], "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            current_end_date = datetime.strptime(current[1], "%Y-%m-%d %H:%M:%S")
        new_end_date = max(current_end_date, datetime.now()) + timedelta(days=days)
    else:
        new_end_date = datetime.now() + timedelta(days=days)
    c.execute(
        "UPDATE users SET subscription = 1, sub_end_date = ? WHERE user_id = ?",
        (new_end_date.strftime("%Y-%m-%d %H:%M:%S.%f"), user_id),
    )
    conn.commit()
    conn.close()
    return new_end_date


def check_subscription(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT subscription, sub_end_date FROM users WHERE user_id = ?", (user_id,)
    )
    result = c.fetchone()
    conn.close()
    if result and result[0] == 1 and result[1]:
        try:
            sub_end_date = datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S.%f")
            return sub_end_date > datetime.now()
        except ValueError:
            sub_end_date = datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S")
            return sub_end_date > datetime.now()
    return False


def delete_active_invoices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE payments SET status = 'expired' WHERE status = 'pending'")
    count = c.rowcount
    conn.commit()
    conn.close()
    return count


def get_users_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_active_subscriptions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM users WHERE subscription = 1 AND sub_end_date > ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),),
    )
    count = c.fetchone()[0]
    conn.close()
    return count


def get_active_paid_payments(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT user_id, amount, days, status, created_at FROM payments WHERE status IN ('pending', 'paid') ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    payments = c.fetchall()
    conn.close()
    return payments


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]


def save_recovery_request(user_id, phone_number, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO recovery_requests (user_id, phone_number, status, created_at) VALUES (?, ?, ?, ?)",
        (user_id, phone_number, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def check_recovery_cooldown(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT created_at, status FROM recovery_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    last_request = c.fetchone()
    conn.close()
    if last_request and last_request[1] == "sent":
        last_time = datetime.strptime(last_request[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_time < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - (datetime.now() - last_time)
            return False, remaining
    return True, None


def check_snosing_cooldown(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT next_snuser_usage FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        next_usage = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < next_usage:
            remaining = next_usage - datetime.now()
            return False, remaining
    return True, None


def update_snosing_cooldown(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    next_usage = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "UPDATE users SET next_snuser_usage = ? WHERE user_id = ?",
        (next_usage, user_id),
    )
    conn.commit()
    conn.close()
    return next_usage


def set_bot_status(enabled: bool):
    global BOT_ENABLED
    BOT_ENABLED = enabled
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)",
        ("bot_enabled", str(int(enabled))),
    )
    conn.commit()
    conn.close()


def get_bot_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT setting_value FROM bot_settings WHERE setting_key = "bot_enabled"'
    )
    result = c.fetchone()
    conn.close()
    return bool(int(result[0])) if result else True


async def notify_all_users(message_text):
    users = get_all_users()
    for user_id in users:
        try:
            await bot.send_message(user_id, message_text, parse_mode=ParseMode.HTML)
        except:
            continue


async def send_recovery_request(phone_number, recovery_data, index):
    url = "https://telegram.org/support?setln=ru"
    text = recovery_data["text"].format(number=phone_number)
    data = {"text": text}
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image podpiskiimage/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
                ssl=False,
            ) as response:
                if response.status in [200, 201, 202, 204]:
                    print(
                        f"{Fore.GREEN}[#{index+1}] Успешно отправлено!{Style.RESET_ALL}"
                    )
                    return "sent"
                else:
                    print(
                        f"{Fore.RED}[-] Ошибка: код {response.status}{Style.RESET_ALL}"
                    )
                    return "failed"
    except Exception as e:
        print(f"{Fore.RED}[-] Ошибка при отправке: {e}{Style.RESET_ALL}")
        return "failed"


def compile_link(pattern: str) -> re.Pattern:
    return re.compile(pattern)


async def send_report_message(link: str, api_id: int, api_hash: str) -> dict:
    message_link_pattern = compile_link(
        r"https://t.me/(?P<username_or_chat>.+)/(?P<message_id>\d+)"
    )
    match = message_link_pattern.search(link)

    if not match:
        logging.error(f"Неправильная ссылка: {link}")
        print(f"{Fore.RED}Неправильная ссылка: {link}{Style.RESET_ALL}")
        return {"success": 0, "failed": 1}

    chat = match.group("username_or_chat")
    message_id = int(match.group("message_id"))

    # Проверяем наличие сессий
    try:
        files = os.listdir(SESSIONS_PATH)
        sessions = [s for s in files if s.endswith(".session")]
        if not sessions:
            logging.error(f"Сессий в папке {SESSIONS_PATH} нет")
            print(f"{Fore.RED}Сессий в папке {SESSIONS_PATH} нет{Style.RESET_ALL}")
            return {"success": 0, "failed": 1}
        else:
            print(f"{Fore.CYAN}Найдено сессий: {len(sessions)}{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"Не удалось открыть папку с сессиями {SESSIONS_PATH}: {e}")
        print(
            f"{Fore.RED}Не удалось открыть папку с сессиями {SESSIONS_PATH}: {e}{Style.RESET_ALL}"
        )
        return {"success": 0, "failed": 1}

    success_count = 0
    failed_count = 0

    for session in sessions:
        client = TelegramClient(f"{SESSIONS_PATH}/{session}", api_id, api_hash)
        print(f"{Fore.YELLOW}Попытка подключения к сессии: {session}{Style.RESET_ALL}")

        try:
            # Подключаемся с тайм-аутом
            await asyncio.wait_for(client.connect(), timeout=10)
            print(f"{Fore.GREEN}Подключение к {session} выполнено{Style.RESET_ALL}")

            # Проверяем авторизацию
            if not await client.is_user_authorized():
                logging.warning(f"Сессия {session} не авторизована")
                print(
                    f"{Fore.RED}Сессия {session} не авторизована, переходим к следующей{Style.RESET_ALL}"
                )
                failed_count += 1
                await client.disconnect()
                continue

            print(f"{Fore.GREEN}Сессия {session} авторизована{Style.RESET_ALL}")

            # Получаем сущность чата
            try:
                entity = await asyncio.wait_for(client.get_entity(chat), timeout=10)
                print(f"{Fore.GREEN}Чат {chat} успешно найден{Style.RESET_ALL}")
            except Exception as e:
                logging.error(f"Не удалось найти чат {chat}: {e}")
                print(
                    f"{Fore.RED}Не удалось найти чат {chat} для {session}: {e}, переходим к следующей сессии{Style.RESET_ALL}"
                )
                failed_count += 1
                await client.disconnect()
                continue

            # Отправляем жалобу
            random.shuffle(REPORT_MESSAGES)
            report_message_text = random.choice(REPORT_MESSAGES)
            print(
                f"{Fore.YELLOW}Отправка жалобы от {session} на сообщение {message_id}{Style.RESET_ALL}"
            )

            await asyncio.wait_for(
                client(
                    ReportRequest(
                        peer=entity,
                        id=[message_id],
                        option="1",
                        message=report_message_text,
                    )
                ),
                timeout=10,
            )
            success_count += 1
            logging.info(f"Жалоба от {session} на {link} успешно отправлена")
            print(
                f"{Fore.GREEN}Жалоба от {session} на {link} успешно отправлена{Style.RESET_ALL}"
            )

            # Успех — отключаемся и завершаем
            await client.disconnect()
            break

        except asyncio.TimeoutError:
            failed_count += 1
            logging.error(f"Тайм-аут при работе с {session}")
            print(
                f"{Fore.RED}Тайм-аут при работе с {session}, переходим к следующей сессии{Style.RESET_ALL}"
            )

        except Exception as e:
            failed_count += 1
            logging.error(f"Ошибка при работе с {session} на {link}: {e}")
            print(
                f"{Fore.RED}Ошибка при работе с {session} на {link}: {e}, переходим к следующей сессии{Style.RESET_ALL}"
            )

        finally:
            if client.is_connected():
                await client.disconnect()
                print(f"{Fore.YELLOW}Сессия {session} отключена{Style.RESET_ALL}")
            await asyncio.sleep(1)  # Пауза перед следующей сессией

    logging.info(
        f"Отправка жалоб для {link} завершена: Успешно={success_count}, Неудачно={failed_count}"
    )
    print(
        f"{Fore.CYAN}Отправка жалоб для {link} завершена: Успешно={success_count}, Неудачно={failed_count}{Style.RESET_ALL}"
    )
    return {"success": success_count, "failed": failed_count}


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    if not BOT_ENABLED:
        await message.answer(
            "<b>🤖 Бот временно отключен администратором!</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    user_name = message.from_user.first_name
    welcome_text, keyboard = get_main_menu(user_name)
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "🔒 <b>У вас нет доступа к админ-панели!</b>", parse_mode=ParseMode.HTML
        )
        return
    users_count = get_users_count()
    active_subs = get_active_subscriptions()
    bot_status = "✅ Включен" if BOT_ENABLED else "❌ Выключен"
    admin_text = (
        "🌟 <b>Админ-панель</b> 🌟\n"
        "══════════════════════\n"
        f"👥 <b>Пользователей:</b> {users_count}\n"
        f"✅ <b>Активных подписок:</b> {active_subs}\n"
        f"🤖 <b>Статус бота:</b> {bot_status}\n"
        f"📅 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        "══════════════════════\n"
        "<i>Выберите действие ниже:</i>"
    )
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Выдать подписку", callback_data="admin_give_sub"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить счета", callback_data="admin_delete_invoices"
                ),
            ],
            [
                InlineKeyboardButton(text="💸 Платежи", callback_data="admin_payments"),
                InlineKeyboardButton(text="👤 Подписчики", callback_data="admin_users"),
            ],
            [InlineKeyboardButton(text="🔛 Вкл/Выкл бота", callback_data="toggle_bot")],
            [InlineKeyboardButton(text="🔙 Выйти", callback_data="back")],
        ]
    )
    await message.answer(
        admin_text, parse_mode=ParseMode.HTML, reply_markup=admin_keyboard
    )


@dp.callback_query()
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance, subscription, sub_end_date, next_snuser_usage = get_user_data(user_id)
    subscription_active = check_subscription(user_id)

    is_admin_action = (
        callback.data
        in [
            "admin_give_sub",
            "admin_delete_invoices",
            "admin_payments",
            "admin_users",
            "toggle_bot",
            "admin_panel",
        ]
        or callback.data.startswith("view_user_")
        or callback.data.startswith("give_sub_")
        or callback.data.startswith("set_sub_")
        or callback.data.startswith("user_payments_")
    )

    if not BOT_ENABLED and not is_admin_action and callback.data != "back":
        await callback.answer(
            "🤖 Бот временно отключен администратором!", show_alert=True
        )
        return

    if callback.data == "profile":
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass
        username = callback.from_user.username or "Не указан"
        profile_text, profile_keyboard = get_profile_menu(
            username, user_id, balance, subscription, sub_end_date
        )
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(PHOTO_PATH),
            caption=profile_text,
            parse_mode=ParseMode.HTML,
            reply_markup=profile_keyboard,
        )

    elif callback.data == "tasks":
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass
        tasks_text = "<b>🪄 Раздел задач</b>\n\n" "<i>👉 Выберите нужный раздел:</i>"
        tasks_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🛠 Сносинг", callback_data="snosing"),
                    InlineKeyboardButton(
                        text="🔄 Восстановление", callback_data="recovery"
                    ),
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
            ]
        )
        await bot.send_message(
            callback.message.chat.id,
            tasks_text,
            parse_mode=ParseMode.HTML,
            reply_markup=tasks_keyboard,
        )

    elif callback.data == "subscribe":
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass
        subscribe_text = "<b>Выберите срок подписки:</b>"
        subscribe_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="1 день (1$) 🗓", callback_data="sub_1"),
                    InlineKeyboardButton(text="3 дня (3$) 📅", callback_data="sub_3"),
                ],
                [
                    InlineKeyboardButton(text="5 дней (5$) 📆", callback_data="sub_5"),
                    InlineKeyboardButton(
                        text="10 дней (10$) 📆", callback_data="sub_10"
                    ),
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back")],
            ]
        )
        await bot.send_message(
            callback.message.chat.id,
            subscribe_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subscribe_keyboard,
        )

    elif callback.data.startswith("sub_"):
        days = int(callback.data.split("_")[1])
        amount = float(days)
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass

        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=amount,
            allow_anonymous=False,
            allow_comments=False,
            description=f"💳 Подписка\n👤 Пользователь: ID {user_id}\n📅 Дней: {days}\n💸 Сумма: {amount}$ (USDT)\n⏰ Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )
        pay_url = invoice.bot_invoice_url
        invoice_id = str(invoice.invoice_id)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT OR REPLACE INTO payments (check_id, user_id, amount, days, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (invoice_id, user_id, amount, days, "pending", timestamp),
        )
        conn.commit()
        conn.close()

        payment_text = (
            f"<b>[💳] Покупка подписки</b>\n\n"
            f"<i>Детали платежа:</i>\n"
            f"<blockquote>"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📅 Дней: <code>{days}</code>\n"
            f"💸 Сумма: <code>{amount}$</code>\n"
            f"📡 Статус: <b>Ожидает оплаты</b>\n"
            f"⏰ Дата: <code>{timestamp}</code>\n"
            f"💱 Валюта: <b>USDT</b>\n"
            f"</blockquote>"
        )
        payment_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🤍 Оплатить", url=pay_url),
                    InlineKeyboardButton(
                        text="🖤 Проверить", callback_data=f"check_sub_{invoice_id}"
                    ),
                ],
                [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_sub")],
            ]
        )

        msg = await bot.send_message(
            callback.message.chat.id,
            payment_text,
            parse_mode=ParseMode.HTML,
            reply_markup=payment_keyboard,
        )
        asyncio.create_task(
            check_payment_after_delay(
                callback, invoice_id, days, amount, msg.message_id
            )
        )

    elif callback.data.startswith("check_sub_"):
        invoice_id = callback.data.split("_")[2]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT user_id, days, amount, status FROM payments WHERE check_id = ?",
            (invoice_id,),
        )
        payment = c.fetchone()
        conn.close()

        if payment and payment[3] == "pending":
            invoices = await crypto.get_invoices(invoice_ids=invoice_id)
            invoice_status = invoices[0]
            if invoice_status.status == "paid":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(
                    "UPDATE payments SET status = 'paid' WHERE check_id = ?",
                    (invoice_id,),
                )
                new_end_date = set_subscription(payment[0], payment[1])
                conn.commit()
                conn.close()
                try:
                    await bot.delete_message(
                        callback.message.chat.id, callback.message.message_id
                    )
                except:
                    pass
                await bot.send_message(
                    callback.message.chat.id,
                    f"<b>[✅] Подписка на {payment[1]} дней активирована!</b>\n"
                    f"Действует до: {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🔙 Назад", callback_data="back"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await callback.answer(
                    "💔 <b>Ошибка! Счет не оплачен!</b>", show_alert=True
                )

    elif callback.data == "cancel_sub":
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass
        user_name = callback.from_user.first_name
        welcome_text, keyboard = get_main_menu(user_name)
        await bot.send_message(
            callback.message.chat.id,
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    elif callback.data == "recovery":
        if not subscription_active:
            if subscription == 1 and sub_end_date:
                await callback.message.edit_text(
                    text="<b>💔 Ваша подписка истекла!</b>\n<blockquote><i>Обновите подписку для доступа.</i></blockquote>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                        ]
                    ),
                )
            else:
                await callback.message.edit_text(
                    text="<b>❌ У вас нет активной подписки!</b>\n<blockquote><i>Приобретите подписку для доступа.</i></blockquote>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                        ]
                    ),
                )
            return
        can_recover, remaining = check_recovery_cooldown(user_id)
        if not can_recover:
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            await callback.message.edit_text(
                text=f"<b>⏳ Подождите!</b>\n<blockquote><i>Следующее восстановление через {minutes} мин {seconds} сек</i></blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )
            return
        await callback.message.edit_text(
            text="<b>🔄 Восстановление</b>\n\n<i>Введите номер телефона (например, +380631234567):</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                ]
            ),
        )
        await state.set_state(RecoveryStates.waiting_for_phone)

    elif callback.data == "snosing":
        if not subscription_active:
            await callback.message.edit_text(
                text="<b>❌ У вас нет активной подписки!</b>\n<blockquote><i>Приобретите подписку для доступа.</i></blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                    ]
                ),
            )
            return

        can_snos, remaining = check_snosing_cooldown(user_id)
        if not can_snos:
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            await callback.message.edit_text(
                f"<b>⏳ Подождите!</b>\n<blockquote><i>Следующий снос через {minutes} мин {seconds} сек</i></blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )
            return

        await callback.message.edit_text(
            "<blockquote><b>[📥] Отправка репортов:</b></blockquote>\n\n<i>Отправьте ссылку на сообщение из публичной группы</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                ]
            ),
        )
        await state.set_state(SnosingStates.waiting_for_link)

    elif callback.data == "back":
        await state.clear()
        try:
            await bot.delete_message(
                callback.message.chat.id, callback.message.message_id
            )
        except:
            pass
        user_name = callback.from_user.first_name
        welcome_text, keyboard = get_main_menu(user_name)
        await bot.send_message(
            callback.message.chat.id,
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    elif callback.data == "admin_give_sub":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            "🎁 <b>Выдача подписки</b>\n\n<i>Формат:</i> /give_sub <user_id> <days>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            ),
        )

    elif callback.data == "admin_delete_invoices":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        count = delete_active_invoices()
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            f"🗑 <b>Удалено счетов:</b> {count}\n<i>Все активные счета очищены!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            ),
        )

    elif callback.data == "admin_payments":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        payments = get_active_paid_payments()
        payment_text = (
            "💸 <b>Активные и оплаченные платежи</b>\n══════════════════════\n"
        )
        if not payments:
            payment_text += "<i>Нет активных или оплаченных платежей</i>"
        for p in payments:
            status_emoji = "✅" if p[3] == "paid" else "⏳"
            payment_text += (
                f"{status_emoji} <b>ID:</b> {p[0]}\n"
                f"💰 {p[1]}$ за {p[2]} дней\n"
                f"🕒 {p[4]}\n"
                "──────────────\n"
            )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            payment_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            ),
        )

    elif callback.data == "admin_users":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        users = get_all_users()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for user_id in users[:10]:
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"ID: {user_id}", callback_data=f"view_user_{user_id}"
                    )
                ]
            )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            "👤 <b>Список подписчиков</b>\n<i>Выберите пользователя:</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    elif callback.data.startswith("view_user_"):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        target_user_id = int(callback.data.split("_")[2])
        balance, subscription, sub_end_date, _ = get_user_data(target_user_id)
        sub_status = (
            "✅ Активна" if check_subscription(target_user_id) else "❌ Не активна"
        )
        user_info = (
            f"<b>👤 Информация о пользователе</b>\n"
            f"══════════════════════\n"
            f"<b>🆔 ID:</b> <code>{target_user_id}</code>\n"
            f"<b>💰 Баланс:</b> {balance}$\n"
            f"<b>📅 Подписка:</b> {sub_status}\n"
            f"<b>⏰ Окончание:</b> {sub_end_date or 'Нет'}\n"
            f"══════════════════════\n"
            f"<i>Выберите действие:</i>"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎁 Выдать подписку",
                        callback_data=f"give_sub_{target_user_id}",
                    ),
                    InlineKeyboardButton(
                        text="💸 Платежи",
                        callback_data=f"user_payments_{target_user_id}",
                    ),
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")],
            ]
        )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            user_info,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    elif callback.data.startswith("give_sub_"):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        target_user_id = int(callback.data.split("_")[2])
        sub_text = (
            f"<b>🎁 Выдача подписки для ID {target_user_id}</b>\n"
            f"<i>Выберите срок:</i>"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="1 день", callback_data=f"set_sub_{target_user_id}_1"
                    ),
                    InlineKeyboardButton(
                        text="3 дня", callback_data=f"set_sub_{target_user_id}_3"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="5 дней", callback_data=f"set_sub_{target_user_id}_5"
                    ),
                    InlineKeyboardButton(
                        text="10 дней", callback_data=f"set_sub_{target_user_id}_10"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", callback_data=f"view_user_{target_user_id}"
                    )
                ],
            ]
        )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            sub_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )

    elif callback.data.startswith("set_sub_"):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        parts = callback.data.split("_")
        target_user_id = int(parts[2])
        days = int(parts[3])
        new_end_date = set_subscription(target_user_id, days)
        target_user = await bot.get_chat(target_user_id)
        target_user_name = target_user.first_name or "Пользователь"
        response_text = (
            f"<b>🎁 Подписка выдана!</b>\n\n"
            f"<i>Информация:</i>\n"
            f"<blockquote>"
            f"👤 <b>Кому:</b> {target_user_name} (ID: {target_user_id})\n"
            f"📅 <b>До:</b> {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            f"</blockquote>"
        )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад", callback_data=f"view_user_{target_user_id}"
                        )
                    ]
                ]
            ),
        )

    elif callback.data.startswith("user_payments_"):
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        target_user_id = int(callback.data.split("_")[2])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT user_id, amount, days, status, created_at FROM payments WHERE user_id = ? AND status IN ('pending', 'paid') ORDER BY created_at DESC LIMIT 5",
            (target_user_id,),
        )
        payments = c.fetchall()
        conn.close()
        payment_text = f"<b>💸 Платежи пользователя ID {target_user_id}</b>\n══════════════════════\n"
        if not payments:
            payment_text += "<i>Нет активных или оплаченных платежей</i>"
        for p in payments:
            status_emoji = "✅" if p[3] == "paid" else "⏳"
            payment_text += (
                f"{status_emoji} <b>ID:</b> {p[0]}\n"
                f"💰 {p[1]}$ за {p[2]} дней\n"
                f"🕒 {p[4]}\n"
                "──────────────\n"
            )
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(
            callback.message.chat.id,
            payment_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад", callback_data=f"view_user_{target_user_id}"
                        )
                    ]
                ]
            ),
        )

    elif callback.data == "admin_panel":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        await bot.delete_message(callback.message.chat.id, callback.message.message_id)
        users_count = get_users_count()
        active_subs = get_active_subscriptions()
        bot_status = "✅ Включен" if BOT_ENABLED else "❌ Выключен"
        admin_text = (
            "🌟 <b>Админ-панель</b> 🌟\n"
            "══════════════════════\n"
            f"👥 <b>Пользователей:</b> {users_count}\n"
            f"✅ <b>Активных подписок:</b> {active_subs}\n"
            f"🤖 <b>Статус бота:</b> {bot_status}\n"
            f"📅 <b>Дата:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "══════════════════════\n"
            "<i>Выберите действие ниже:</i>"
        )
        admin_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎁 Выдать подписку", callback_data="admin_give_sub"
                    ),
                    InlineKeyboardButton(
                        text="🗑 Удалить счета", callback_data="admin_delete_invoices"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="💸 Платежи", callback_data="admin_payments"
                    ),
                    InlineKeyboardButton(
                        text="👤 Подписчики", callback_data="admin_users"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="🔛 Вкл/Выкл бота", callback_data="toggle_bot"
                    )
                ],
                [InlineKeyboardButton(text="🔙 Выйти", callback_data="back")],
            ]
        )
        await bot.send_message(
            callback.message.chat.id,
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_keyboard,
        )

    elif callback.data == "toggle_bot":
        if callback.from_user.id != ADMIN_ID:
            await callback.answer("🔒 <b>Нет доступа!</b>", show_alert=True)
            return
        new_status = not BOT_ENABLED
        set_bot_status(new_status)
        status_text = "включен" if new_status else "выключен"
        await bot.edit_message_text(
            f"🤖 <b>Бот {status_text}!</b>",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
                ]
            ),
        )
        await notify_all_users(
            f"<b>🤖 Бот {status_text} администратором!</b>\n"
            f"{'Все функции снова доступны!' if new_status else 'Все функции временно недоступны.'}"
        )

    await callback.answer()


@dp.message(RecoveryStates.waiting_for_phone)
async def handle_recovery(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    subscription_active = check_subscription(user_id)
    balance, subscription, sub_end_date, _ = get_user_data(user_id)

    if not subscription_active:
        if subscription == 1 and sub_end_date:
            await message.answer(
                "<b>💔 Ваша подписка истекла!</b>\n<blockquote><i>Обновите подписку для доступа.</i></blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                    ]
                ),
            )
        else:
            await message.answer(
                "<b>❌ У вас нет активной подписки!</b>\n<blockquote><i>Приобретите подписку для доступа.</i></blockquote>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                    ]
                ),
            )
        await state.clear()
        return

    can_recover, remaining = check_recovery_cooldown(user_id)
    if not can_recover:
        minutes, seconds = divmod(int(remaining.total_seconds()), 60)
        await message.answer(
            f"<b>⏳ Подождите!</b>\n<blockquote><i>Следующее восстановление через {minutes} мин {seconds} сек</i></blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                ]
            ),
        )
        await state.clear()
        return

    phone_number = message.text.strip()
    if not phone_number.startswith("+") or not phone_number[1:].isdigit():
        await message.answer(
            "<b>❌ Неверный формат номера!</b>\n<i>Введите номер в формате +380631234567</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                ]
            ),
        )
        return

    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    wait_msg = await bot.send_message(
        message.chat.id,
        "<b>Заявка подана, ожидайте…</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
            ]
        ),
    )

    sent_count = 0
    failed_count = 0
    total_requests = len(RECOVERY_TEXTS)

    for i, recovery_data in enumerate(RECOVERY_TEXTS):
        status = await send_recovery_request(phone_number, recovery_data, i)
        save_recovery_request(user_id, phone_number, status)
        if status == "sent":
            sent_count += 1
        else:
            failed_count += 1

        progress_text = (
            f"<b>Заявка подана, ожидайте…</b>\n\n"
            f"<i>Прогресс:</i>\n"
            f"<blockquote>"
            f"📤 Отправлено: {sent_count}/{total_requests}\n"
            f"❌ Не отправлено: {failed_count}\n"
            f"</blockquote>"
        )
        try:
            await bot.edit_message_text(
                progress_text,
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )
        except:
            wait_msg = await bot.send_message(
                message.chat.id,
                progress_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )

        if i < total_requests - 1:
            await asyncio.sleep(5)

    result_text = (
        "<b>✅ Все заявки обработаны!</b>\n\n"
        "<i>📌 Информация:</i>\n"
        "<blockquote>"
        f"- 📞 Номер телефона: <code>{phone_number}</code>\n"
        f"- 📤 Подано заявок: {sent_count}\n"
        f"- ❌ Не отправлено: {failed_count}\n"
        "</blockquote>"
    )
    try:
        await bot.edit_message_text(
            result_text,
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🙈 Скрыть", callback_data="back")]
                ]
            ),
        )
    except:
        await bot.send_message(
            message.chat.id,
            result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🙈 Скрыть", callback_data="back")]
                ]
            ),
        )
    await state.clear()


@dp.message(SnosingStates.waiting_for_link)
async def handle_snosing(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    subscription_active = check_subscription(user_id)

    if not subscription_active:
        await message.answer(
            "<b>❌ У вас нет активной подписки!</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
                ]
            ),
        )
        await state.clear()
        return

    can_snos, remaining = check_snosing_cooldown(user_id)
    if not can_snos:
        minutes, seconds = divmod(int(remaining.total_seconds()), 60)
        await message.answer(
            f"<b>⏳ Подождите!</b>\n<blockquote><i>Следующий снос через {minutes} мин {seconds} сек</i></blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                ]
            ),
        )
        await state.clear()
        return

    link = message.text.strip()
    pattern = re.compile(r"https://t.me/(?P<username_or_chat>.+)/(?P<message_id>\d+)")
    if not pattern.search(link):
        await message.answer(
            "❌ Ошибка! Ссылка должна быть в формате: https://t.me/username/message_id",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        await bot.delete_message(message.chat.id, message.message_id - 1)
        await bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    wait_msg = await bot.send_message(
        message.chat.id,
        "<blockquote><b>[📤] Отправка репортов началась!</b></blockquote>\n\n"
        f'<a href="{link}">⛓️‍💥 Ссылка на сообщение</a>\n\n'
        "<i>📊 Результаты будут присланы вам отдельным уведомлением</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="↩ Назад", callback_data="back")]
            ]
        ),
    )

    update_snosing_cooldown(user_id)
    report_result = await send_report_message(link, API_ID, API_HASH)
    success = report_result.get("success", 0)
    failed = report_result.get("failed", 0)

    result_message = (
        "<blockquote><b>[📦] Результаты репортов:</b></blockquote>\n\n"
        f'<a href="{link}">⛓️‍💥 Нарушение</a>\n\n'
        "<b>📊 Информация о репортах:</b>\n"
        "<blockquote>"
        f"🟢 Успешных жалоб: {success}\n"
        f"🔴 Не успешных жалоб: {failed}\n"
        "</blockquote>"
    )

    try:
        await bot.edit_message_text(
            result_message,
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🙈 Скрыть", callback_data="back")]
                ]
            ),
        )
    except:
        await bot.send_message(
            message.chat.id,
            result_message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🙈 Скрыть", callback_data="back")]
                ]
            ),
        )
    await state.clear()


async def check_payment_after_delay(
    callback: types.CallbackQuery,
    invoice_id: str,
    days: int,
    amount: float,
    message_id: int,
):
    await asyncio.sleep(300)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status FROM payments WHERE check_id = ?", (invoice_id,))
    status = c.fetchone()
    if status and status[0] == "pending":
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        invoice_status = invoices[0]
        if invoice_status.status == "paid":
            c.execute(
                "UPDATE payments SET status = 'paid' WHERE check_id = ?", (invoice_id,)
            )
            new_end_date = set_subscription(callback.from_user.id, days)
            conn.commit()
            try:
                await bot.delete_message(callback.message.chat.id, message_id)
            except:
                pass
            await bot.send_message(
                callback.message.chat.id,
                f"<b>[✅] Подписка на {days} дней активирована!</b>\n"
                f"Действует до: {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )
        else:
            c.execute(
                "UPDATE payments SET status = 'expired' WHERE check_id = ?",
                (invoice_id,),
            )
            conn.commit()
            try:
                await bot.delete_message(callback.message.chat.id, message_id)
            except:
                pass
            await bot.send_message(
                callback.message.chat.id,
                f"<b>[⏰] Время оплаты истекло!</b>\nСчет на {amount}$ для подписки на {days} дней более не активен.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
                    ]
                ),
            )
    conn.close()


@dp.message(Command("give_sub"))
async def give_subscription(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "🔒 <b>У вас нет прав на эту команду!</b>", parse_mode=ParseMode.HTML
        )
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Неверный формат команды")
        target_user_id = int(parts[1])
        days = int(parts[2])
        new_end_date = set_subscription(target_user_id, days)
        target_user = await bot.get_chat(target_user_id)
        target_user_name = target_user.first_name or "Пользователь"
        response_text = (
            f"<b>🎁 Подписка выдана!</b>\n\n"
            f"<i>Информация:</i>\n"
            f"<blockquote>"
            f"👤 <b>Кому:</b> {target_user_name} (ID: {target_user_id})\n"
            f"📅 <b>До:</b> {new_end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            f"</blockquote>"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
            ]
        )
        await bot.send_message(
            message.chat.id,
            response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
    except ValueError as e:
        await message.answer(
            f"❌ <b>Ошибка:</b> {str(e)}. Использование: /give_sub <user_id> <days>",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass


async def main():
    init_db()
    global BOT_ENABLED
    BOT_ENABLED = get_bot_status()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
