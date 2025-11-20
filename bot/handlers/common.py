from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.database.database import db
from bot.keyboards.reply import get_main_keyboard
from bot.filters.custom_filters import IsPrivateFilter
from bot.config import config
from bot.utils.logger import logger

router = Router()
router.message.filter(IsPrivateFilter())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    logger.info(f"User {message.from_user.id} started the bot")
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Это бот для управления карточками товаров.\n\n"
        "Используй кнопки меню для взаимодействия:",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Помощь</b>\n\n"
        "🔹 <b>Добавить карточку</b> - создать новую карточку товара\n"
        "🔹 <b>Посмотреть карточки</b> - просмотреть все одобренные карточки\n"
        "🔹 <b>Баланс</b> - просмотреть баланс и вывести средства\n\n"
    )
    
    if message.from_user.id in config.ADMIN_IDS:
        help_text += (
            "👨‍💼 <b>Админ функции:</b>\n"
            "🔹 <b>Модерация</b> - модерировать карточки пользователей\n"
            "🔹 <b>Статистика</b> - просмотреть статистику пользователей\n"
            "🔹 <b>Заявки на вывод</b> - обработать заявки на вывод средств\n"
        )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять.")
        return
    
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    logger.info(f"User {message.from_user.id} cancelled action from state {current_state}")
    
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )