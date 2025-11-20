import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "").split(",") if id_]
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/telegram_bot")
    PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")
    
    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in environment variables")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS is not set in environment variables")


config = Config()