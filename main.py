import asyncio
import logging
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatPermissions

# --- КОНФИГУРАЦИЯ ---
TOKEN = "7358358931:AAGDN7N7mv1m_9v54t0RLZYy6L81vQ-6n9A"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище варнов (в оперативной памяти)
warns_storage = {}

# Правила MyFine ✨ (минуты, описание)
RULES = {
    "1": (180, "Мат (3 часа)"),
    "2": (300, "Оскорбления (5 часов)"),
    "3": (120, "Спам (2 часа)"),
    "4": (1440, "Контент 18+/Запрещенка (24 часа)"),
    "5": (60, "Оффтоп (Варн / 1 час)"),
    "6": (240, "Флейм/Провокация (4 часа)"),
    "7": (360, "Реклама (6 часов)")
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def is_admin(chat_id: int, user_id: int):
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in ["administrator", "creator"]

# --- ОБРАБОТКА WEB APP DATA ---
@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    """Принимает данные из твоего HTML-файла"""
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.answer("❌ У вас нет прав администратора.")

    try:
        data = json.loads(message.web_app_data.data)
        target = data.get("target")
        rule_id = data.get("rule")
        custom_min = data.get("custom_minutes")

        # Пытаемся определить ID пользователя
        try:
            user_id = int(target) if target.replace('@', '').isdigit() else target
        except:
            user_id = target

        # Логика времени
        if rule_id == "custom" and custom_min:
            duration = int(custom_min)
            label = "Кастомное наказание"
        else:
            duration, label = RULES.get(rule_id, (60, "Нарушение правил"))

        # Специальная проверка варнов для оффтопа через WebApp
        if rule_id == "5":
            current_warns = warns_storage.get(user_id, 0) + 1
            if current_warns < 3:
                warns_storage[user_id] = current_warns
                return await message.answer(f"ℹ️ Варн выдан пользователю {target} (Оффтоп: {current_warns}/3)")
            else:
                warns_storage[user_id] = 0
                label = "Систематический оффтоп (3 варна)"

        until = datetime.now() + timedelta(minutes=duration)
        
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id, # Работает, если бот "видел" этого юзера ранее
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await message.answer(f"✅ **Действие через WebApp**\nОбъект: {target}\nПричина: {label}\nСрок: {duration} мин.")

    except Exception as e:
        await message.answer(f"❌ Ошибка WebApp: {e}")

# --- КОМАНДЫ МОДЕРАЦИИ (ТЕКСТОВЫЕ) ---
@dp.message(Command("mute"))
async def cmd_mute(message: types.Message, command: CommandObject):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.answer("Ответьте на сообщение человека командой `/mute 1`")

    rule_id = command.args
    if not rule_id or rule_id not in RULES:
        return await message.answer("Укажите номер правила (1-7)")

    user_id = message.reply_to_message.from_user.id
    duration, label = RULES[rule_id]

    # Логика варнов для правила 5
    if rule_id == "5":
        warns = warns_storage.get(user_id, 0) + 1
        if warns < 3:
            warns_storage[user_id] = warns
            return await message.answer(f"⚠️ Варн за оффтоп! ({warns}/3)")
        warns_storage[user_id] = 0
        label = "Оффтоп (накоплено 3 варна)"

    until = datetime.now() + timedelta(minutes=duration)
    await bot.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
    await message.answer(f"🚫 {message.reply_to_message.from_user.first_name} замучен на {duration} мин. ({label})")
    await bot.delete_message(message.chat.id, message.reply_to_message.message_id)

@dp.message(Command("unwarn"))
async def cmd_unwarn(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        warns_storage[uid] = 0
        await message.answer("✅ Варны обнулены.")

# --- ЗАПУСК ---
async def main():
    print("Бот MyFine запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())