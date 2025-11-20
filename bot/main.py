import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database.database import db
from bot.handlers import common, user, payment, admin
from bot.utils.logger import logger


async def main():
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    await db.init_db()
    
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    
    logger.info("Bot started successfully")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")