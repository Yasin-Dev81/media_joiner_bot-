from decouple import config
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = config("BOT_TOKEN")
PORT = config("PORT", default=8080, cast=int)
WEBHOOK_URL = config("WEBHOOK_URL", default=None)
