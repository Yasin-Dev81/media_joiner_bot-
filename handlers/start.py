from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from html import escape


router = Router(name="commands-router")


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        f"👋 سلام {escape(message.from_user.first_name)}\n\n"
        f"📸 میتونی الان یه عکس یا یه ویدیو برام بفرستی 🎥"
    )
    await message.answer("Powered by @farazom")


def register_commands(dp: Dispatcher):
    dp.include_router(router)
