import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ================= НАСТРОЙКИ =================
TOKEN = "7358358931:AAGDN7N7mv1m_9v54t0RLZYy6L81vQ-6n9A"
TARGET_GROUP_ID = -1002912470569 
YOUTUBE_URL = "https://www.youtube.com/@MineFine_YT"

# Список зарегистрированных админов
USERS_DB = {"nullkotek": "kotek", "kisyna123": "kisyna", "hazbi": "hazbi"}
LOG_FILE = "admin_logs.txt"
WARNS_FILE = "warns.json"
# =============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

user_id_map = {} 
user_name_cache = {}

class Form(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_target = State()
    waiting_for_broadcast = State()
    waiting_for_warn_target = State()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def load_warns():
    if os.path.exists(WARNS_FILE):
        with open(WARNS_FILE, "r") as f: return json.load(f)
    return {}

def save_warns(warns):
    with open(WARNS_FILE, "w") as f: json.dump(warns, f)

def log_action(admin, action, target, extra=""):
    time = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time}] {admin} -> {action} {target} {extra}\n")

# --- ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ ---
def get_main_dashboard():
    kb = [
        [InlineKeyboardButton(text="👥 МОДЕРАЦИЯ (АДМИНЫ)", callback_data="show_admins")],
        [InlineKeyboardButton(text="🤬 МУТ", callback_data="btn_mute"), InlineKeyboardButton(text="⚠️ ВАРН", callback_data="btn_warn")],
        [InlineKeyboardButton(text="📡 СДЕЛАТЬ РАССЫЛКУ", callback_data="btn_broadcast")],
        [InlineKeyboardButton(text="📜 ЛОГИ", callback_data="btn_logs"), InlineKeyboardButton(text="📺 YOUTUBE", url=YOUTUBE_URL)],
        [InlineKeyboardButton(text="🚪 ЗАВЕРШИТЬ СЕАНС", callback_data="logout")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- ОБРАБОТКА ДАННЫХ В ГРУППЕ ---
@dp.message(F.chat.id == TARGET_GROUP_ID)
async def track_users(message: types.Message):
    if message.from_user:
        uid = str(message.from_user.id)
        uname = message.from_user.username.lower() if message.from_user.username else None
        user_name_cache[uid] = message.from_user.full_name
        if uname: user_id_map[uname] = uid

# --- ЛОГИКА АВТОРИЗАЦИИ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "<b>CORE SYSTEM: MyFine Admin</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Требуется идентификация сотрудника.\n\n"
        "Нажмите кнопку ниже для начала."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Вход в систему", callback_data="start_auth")]])
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
    try: await message.delete()
    except: pass

@dp.callback_query(F.data == "start_auth")
async def auth_init(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_login)
    await callback.message.edit_text(
        "<b>АВТОРИЗАЦИЯ</b> [ ▬▭▭ ]\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "👤 Введите ваш <b>логин:</b>", 
        parse_mode="HTML"
    )

@dp.message(Form.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(Form.waiting_for_password)
    try: await message.delete()
    except: pass
    await message.answer(
        f"<b>АВТОРИЗАЦИЯ</b> [ ▬▬▭ ]\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Логин: <code>{message.text}</code>\n"
        "🔑 Введите ваш <b>пароль:</b>",
        parse_mode="HTML"
    )

@dp.message(Form.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    login_val = data.get("login")
    pass_val = message.text
    try: await message.delete()
    except: pass

    if USERS_DB.get(login_val) == pass_val:
        await state.clear()
        dashboard_text = (
            f"<b>ДОСТУП РАЗРЕШЕН</b> [ ▬▬▬ ]\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"Добро пожаловать, <b>{login_val}</b>.\n"
            "Система авторизована."
        )
        await message.answer(dashboard_text, reply_markup=get_main_dashboard(), parse_mode="HTML")
    else:
        await state.clear()
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Повторить", callback_data="start_auth")]])
        await message.answer("❌ <b>ОШИБКА ДОСТУПА</b>\nДанные не найдены.", reply_markup=kb, parse_mode="HTML")

# --- НОВЫЙ ФУНКЦИОНАЛ: ПРОСМОТР АДМИНОВ ---
@dp.callback_query(F.data == "show_admins")
async def show_admins_list(callback: types.CallbackQuery):
    admins_list = "\n".join([f"• <code>{user}</code>" for user in USERS_DB.keys()])
    text = (
        "<b>БАЗА ДАННЫХ: МОДЕРАЦИЯ</b>\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "Список зарегистрированных администраторов:\n\n"
        f"{admins_list}\n\n"
        "<i>Доступ к изменению базы через конфигурацию.</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 НАЗАД", callback_data="to_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

# --- ОСТАЛЬНЫЕ ФУНКЦИИ (ВАРН, МУТ, РАССЫЛКА) ---
@dp.callback_query(F.data == "btn_warn")
async def start_warn(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_warn_target)
    await callback.message.edit_text("⚠️ <b>ВЫДАЧА ПРЕДУПРЕЖДЕНИЯ</b>\nВведите @username или ID:", parse_mode="HTML")

@dp.message(Form.waiting_for_warn_target)
async def process_warn(message: types.Message, state: FSMContext):
    target_raw = message.text.lower().replace("@", "").strip()
    target_id = target_raw if target_raw.isdigit() else user_id_map.get(target_raw)

    if not target_id:
        await message.answer("❌ Объект не обнаружен.", reply_markup=get_main_dashboard())
        await state.clear()
        return

    warns = load_warns()
    user_warns = warns.get(str(target_id), 0) + 1
    warns[str(target_id)] = user_warns
    save_warns(warns)

    name = user_name_cache.get(str(target_id), target_raw)
    log_action(message.from_user.first_name, "ВАРН", name, f"[{user_warns}/3]")

    if user_warns >= 3:
        try:
            await bot.ban_chat_member(TARGET_GROUP_ID, int(target_id), until_date=datetime.now() + timedelta(days=1))
            warns[str(target_id)] = 0
            save_warns(warns)
            await bot.send_message(TARGET_GROUP_ID, f"🚫 <b>BAN: 3/3 ПРЕДУПРЕЖДЕНИЙ</b>\n👤 Игрок: {name}\nСрок: 24 часа.", parse_mode="HTML")
        except: pass
    else:
        await bot.send_message(TARGET_GROUP_ID, f"⚠️ <b>ПРЕДУПРЕЖДЕНИЕ</b>\n👤 Игрок: {name}\nСтатус: {user_warns}/3", parse_mode="HTML")

    await message.answer(f"✅ Варн выдан ({user_warns}/3)", reply_markup=get_main_dashboard())
    await state.clear()

@dp.callback_query(F.data == "btn_mute")
async def start_mute(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_target)
    await callback.message.edit_text("🤐 <b>УСТАНОВКА МУТА</b>\nВведите @username или ID:", parse_mode="HTML")

@dp.message(Form.waiting_for_target)
async def process_mute_target(message: types.Message, state: FSMContext):
    target_raw = message.text.lower().replace("@", "").strip()
    target_id = target_raw if target_raw.isdigit() else user_id_map.get(target_raw)

    if not target_id:
        await message.answer("❌ Объект не обнаружен.", reply_markup=get_main_dashboard())
        await state.clear()
        return

    await state.update_data(m_id=target_id)
    kb = [
        [InlineKeyboardButton(text="15 мин", callback_data="m_15"), InlineKeyboardButton(text="1 час", callback_data="m_60")],
        [InlineKeyboardButton(text="12 часов", callback_data="m_720"), InlineKeyboardButton(text="Сутки", callback_data="m_1440")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="to_menu")]
    ]
    await message.answer(f"⏳ Срок изоляции для <code>{target_raw}</code>:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")

@dp.callback_query(F.data.startswith("m_"))
async def finish_mute(callback: types.CallbackQuery, state: FSMContext):
    minutes = int(callback.data.split("_")[1])
    data = await state.get_data()
    t_id = data.get("m_id")
    
    try:
        until = datetime.now() + timedelta(minutes=minutes)
        await bot.restrict_chat_member(TARGET_GROUP_ID, int(t_id), permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
        name = user_name_cache.get(str(t_id), f"ID:{t_id}")
        log_action(callback.from_user.first_name, "МУТ", name, f"на {minutes}м")
        await bot.send_message(TARGET_GROUP_ID, f"🔇 <b>РЕЖИМ ТИШИНЫ</b>\n👤 Объект: {name}\n⏳ Срок: {minutes} мин.", parse_mode="HTML")
        await callback.message.edit_text("✅ Мут активирован.", reply_markup=get_main_dashboard())
    except:
        await callback.message.edit_text("❌ Ошибка прав.", reply_markup=get_main_dashboard())
    await state.clear()

@dp.callback_query(F.data == "btn_broadcast")
async def broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_for_broadcast)
    await callback.message.edit_text("📡 <b>ТРАНСЛЯЦИЯ</b>\nВведите текст сообщения:", parse_mode="HTML")

@dp.message(Form.waiting_for_broadcast)
async def do_broadcast(message: types.Message, state: FSMContext):
    try:
        await bot.send_message(TARGET_GROUP_ID, f"📢 <b>ОПОВЕЩЕНИЕ</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n{message.text}\n\n🎬 {YOUTUBE_URL}", parse_mode="HTML")
        await message.answer("✅ Сообщение доставлено.", reply_markup=get_main_dashboard())
    except:
        await message.answer("❌ Ошибка отправки.", reply_markup=get_main_dashboard())
    await state.clear()

@dp.callback_query(F.data == "btn_logs")
async def show_logs(callback: types.CallbackQuery):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            text = "".join(f.readlines()[-8:])
    else: text = "Журнал пуст."
    await callback.message.edit_text(f"📋 <b>ЖУРНАЛ:</b>\n\n<code>{text}</code>", parse_mode="HTML", reply_markup=get_main_dashboard())

@dp.callback_query(F.data == "to_menu")
async def to_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("⚙️ <b>ГЛАВНАЯ ПАНЕЛЬ:</b>", reply_markup=get_main_dashboard(), parse_mode="HTML")

@dp.callback_query(F.data == "logout")
async def logout(callback: types.CallbackQuery):
    await callback.message.edit_text("🔒 <b>Сеанс завершен.</b> /start")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())