from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

active_users = []
start_time = None


@dp.message(Command("start"))
async def start(message: types.Message):

    await message.answer(
        "📦 Omborga Kiritish Bot ishlayapti\n\n"
        "/startmove - tashishni boshlash\n"
        "/id - chat id"
    )


@dp.message(Command("id"))
async def get_id(message: types.Message):

    await message.answer(
        f"📌 Chat ID:\n{message.chat.id}"
    )


@dp.message(Command("startmove"))
async def start_move(message: types.Message):

    global active_users
    global start_time

    active_users = []
    start_time = datetime.now()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qatnashish",
                    callback_data="join_move"
                )
            ]
        ]
    )

    text = (
        "📦 OMBORGA KIRITISH BOSHLANDI\n\n"
        f"🕒 Boshlanish: {start_time.strftime('%H:%M')}\n\n"
        "👷 Qatnashuvchilar:\n"
        "Hozircha yo‘q"
    )

    await message.answer(
        text,
        reply_markup=kb
    )


@dp.callback_query()
async def join_handler(callback: types.CallbackQuery):

    global active_users

    user = callback.from_user.full_name

    if user not in active_users:
        active_users.append(user)

    users_text = "\n".join(
        [f"{i+1}. {name}" for i, name in enumerate(active_users)]
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Qatnashish",
                    callback_data="join_move"
                )
            ]
        ]
    )

    text = (
        "📦 OMBORGA KIRITISH BOSHLANDI\n\n"
        f"🕒 Boshlanish: {start_time.strftime('%H:%M')}\n\n"
        "👷 Qatnashuvchilar:\n"
        f"{users_text}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=kb
    )

    await callback.answer(
        "Siz qatnashdingiz ✅"
    )


async def main():

    print("Bot ishga tushdi...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
