from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import sqlite3
import logging
import os

logging.basicConfig(level=logging.INFO)

# =====================
# SAFE TOKEN (Render ready)
# =====================
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())

ADMIN_ID = 8361915705

# =====================
# DATABASE
# =====================
conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    age TEXT,
    city TEXT,
    phone TEXT,
    exp TEXT,
    skills TEXT,
    goal TEXT,
    status TEXT
)
""")
conn.commit()

# =====================
# FSM
# =====================
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    phone = State()
    exp = State()
    skills = State()
    goal = State()

# =====================
# UI
# =====================
start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🚀 Начать", callback_data="start_work")]
])

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📩 Анкета")],
        [KeyboardButton(text="👤 Личный кабинет")]
    ],
    resize_keyboard=True
)

edit_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Изменить анкету", callback_data="edit")]
])

def admin_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{uid}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{uid}")
        ]
    ])

# =====================
# START
# =====================
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "🚀 Нажмите «Начать», чтобы продолжить",
        parse_mode="HTML",
        reply_markup=start_kb
    )

@dp.callback_query(F.data == "start_work")
async def start_work(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("👇 Выберите действие:", reply_markup=menu)

# =====================
# PROFILE
# =====================
@dp.message(F.text == "👤 Личный кабинет")
async def kabinet(message: Message):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (message.from_user.id,))
    user = cursor.fetchone()

    if user:
        await message.answer(
            f"📋 <b>Ваша анкета</b>\n\n"
            f"👤 Имя: {user[1]}\n"
            f"🎂 Возраст: {user[2]}\n"
            f"🌍 Город: {user[3]}\n"
            f"📊 Статус: {user[8]}",
            parse_mode="HTML",
            reply_markup=edit_kb
        )
    else:
        await message.answer("❌ У вас нет анкеты")

# =====================
# ADMIN PANEL
# =====================
@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM users")
    users_list = cursor.fetchall()

    if not users_list:
        await message.answer("📭 Нет заявок")
        return

    text = "📊 <b>Список заявок:</b>\n\n"
    kb = []

    for u in users_list:
        text += f"👤 {u[1]} | {u[8]}\n"
        kb.append([InlineKeyboardButton(text=f"{u[1]}", callback_data=f"view_{u[0]}")])

    await message.answer(text, parse_mode="HTML",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

# =====================
# VIEW USER
# =====================
@dp.callback_query(F.data.startswith("view_"))
async def view_user(callback: CallbackQuery):
    await callback.answer()

    uid = int(callback.data.split("_")[1])
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cursor.fetchone()

    if not user:
        await callback.message.answer("❌ Не найдено")
        return

    await callback.message.answer(
        f"📩 <b>Заявка</b>\n\n"
        f"👤 Имя: {user[1]}\n"
        f"🎂 Возраст: {user[2]}\n"
        f"🌍 Город: {user[3]}\n"
        f"📞 Телефон: {user[4]}\n"
        f"💼 Опыт: {user[5]}\n"
        f"🛠 Навыки: {user[6]}\n"
        f"🎯 Цель: {user[7]}\n"
        f"📊 Статус: {user[8]}",
        parse_mode="HTML",
        reply_markup=admin_kb(uid)
    )

# =====================
# ACCEPT / REJECT (ANTI FREEZE)
# =====================
@dp.callback_query(F.data.startswith("accept_"))
async def accept(callback: CallbackQuery):
    await callback.answer("Принято")

    uid = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status='Принята' WHERE user_id=?", (uid,))
    conn.commit()

    try:
        await bot.send_message(uid, "🎉 Ваша заявка принята!")
    except:
        pass

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("✅ ПРИНЯТО")
    except:
        pass


@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    await callback.answer("Отклонено")

    uid = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status='Отклонена' WHERE user_id=?", (uid,))
    conn.commit()

    try:
        await bot.send_message(uid, "❌ Ваша заявка отклонена")
    except:
        pass

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("❌ ОТКЛОНЕНО")
    except:
        pass

# =====================
# RUN
# =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())