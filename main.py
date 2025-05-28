import asyncio
import logging
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher, enums
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiostep import Listen

from config import BOT_TOKEN, PORT, WEBHOOK_URL
from handlers import setup_routers
import glv


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def initialize_bot() -> None:
    """Initialize bot, dispatcher, and storage in glv module."""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")

    glv.bot = Bot(
        BOT_TOKEN, default=DefaultBotProperties(parse_mode=enums.ParseMode.HTML)
    )
    glv.storage = MemoryStorage()
    glv.dp = Dispatcher(storage=glv.storage)

    logging.info("Bot, dispatcher, and storage initialized")


def setup_middlewares() -> None:
    """Setup dispatcher middlewares."""
    if hasattr(glv, "dp") and glv.dp:
        glv.dp.message.outer_middleware(Listen())
        logging.info("Middlewares configured")


async def setup_webhook() -> None:
    """Setup webhook for the bot."""
    if hasattr(glv, "bot") and glv.bot and WEBHOOK_URL:
        try:
            await glv.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
            logging.info(f"Webhook set to {WEBHOOK_URL}/webhook")
        except Exception as e:
            logging.error(f"Failed to set webhook: {e}")
            raise


async def on_startup(app: web.Application) -> None:
    """Application startup handler."""
    logging.info("Starting bot application...")
    await setup_webhook()


async def on_shutdown(app: web.Application) -> None:
    """Application shutdown handler."""
    logging.info("Shutting down bot application...")
    await cleanup_resources()


async def cleanup_resources() -> None:
    """Cleanup bot and storage resources."""
    try:
        if hasattr(glv, "bot") and glv.bot:
            await glv.bot.session.close()
            logging.info("Bot session closed")

        if hasattr(glv, "storage") and glv.storage:
            await glv.storage.close()
            logging.info("Storage closed")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def create_web_app() -> web.Application:
    """Create and configure aiohttp web application."""
    app = web.Application()

    if (
        WEBHOOK_URL
        and hasattr(glv, "dp")
        and hasattr(glv, "bot")
        and glv.dp
        and glv.bot
    ):
        # Setup webhook handler
        webhook_handler = SimpleRequestHandler(
            dispatcher=glv.dp,
            bot=glv.bot,
        )
        webhook_handler.register(app, path="/webhook")
        setup_application(app, glv.dp, bot=glv.bot)

        # Register startup and shutdown handlers
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)

    logging.info("Web application configured")
    return app


async def start_webhook_mode() -> None:
    """Start bot in webhook mode."""
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL is required for webhook mode")

    logging.info(f"Starting webhook mode on port {PORT}")

    try:
        app = create_web_app()
        await web._run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logging.error(f"Failed to start webhook server: {e}")
        raise


async def start_polling_mode() -> None:
    """Start bot in polling mode."""
    logging.info("Starting polling mode")

    try:
        if hasattr(glv, "dp") and hasattr(glv, "bot") and glv.dp and glv.bot:
            await glv.dp.start_polling(glv.bot)
        else:
            raise RuntimeError("Bot or dispatcher not initialized")
    except Exception as e:
        logging.error(f"Failed to start polling: {e}")
        raise


def validate_config() -> None:
    """Validate required configuration."""
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN environment variable is required")
        sys.exit(1)

    logging.info(f"Configuration - WEBHOOK_URL: {WEBHOOK_URL}, PORT: {PORT}")


def setup_bot_components() -> None:
    """Setup all bot components."""
    try:
        initialize_bot()

        if hasattr(glv, "dp") and glv.dp:
            setup_routers(glv.dp)
            setup_middlewares()
        else:
            raise RuntimeError("Dispatcher not initialized")

        logging.info("Bot components setup completed")
    except Exception as e:
        logging.error(f"Failed to setup bot components: {e}")
        raise


async def run_bot() -> None:
    """Main bot execution function."""
    try:
        setup_logging()
        validate_config()
        setup_bot_components()

        # Choose mode based on configuration
        if WEBHOOK_URL:
            await start_webhook_mode()
        else:
            await start_polling_mode()

    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        await cleanup_resources()


async def main() -> None:
    """Application entry point."""
    await run_bot()


if __name__ == "__main__":
    print(f"Starting bot - WEBHOOK_URL: {WEBHOOK_URL}, PORT: {PORT}")
    asyncio.run(main())
