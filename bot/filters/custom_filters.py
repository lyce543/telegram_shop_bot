from aiogram.filters import Filter
from aiogram.types import Message
from bot.config import config


class IsAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMIN_IDS


class IsPrivateFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == "private"


class PriceValidationFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        try:
            price = float(message.text.replace(',', '.'))
            return price > 0
        except (ValueError, AttributeError):
            return False


class AmountValidationFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        try:
            amount = float(message.text.replace(',', '.'))
            return amount > 0
        except (ValueError, AttributeError):
            return False