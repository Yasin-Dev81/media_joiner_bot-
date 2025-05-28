from aiogram import Dispatcher

from .media import register_media_handlers
from .start import register_commands


def setup_routers(dp: Dispatcher):
    register_commands(dp)
    register_media_handlers(dp)


__all__ = ("setup_routers",)
