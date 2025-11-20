from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from decimal import Decimal

from bot.database.database import db
from bot.keyboards.reply import get_main_keyboard, get_skip_photo_keyboard, remove_keyboard
from bot.keyboards.inline import get_cards_navigation_keyboard
from bot.filters.custom_filters import IsPrivateFilter, PriceValidationFilter
from bot.states.states import AddCardStates
from bot.config import config
from bot.utils.logger import logger

router = Router()
router.message.filter(IsPrivateFilter())


@router.message(F.text == "➕ Добавить карточку")
async def add_card_start(message: Message, state: FSMContext):
    await state.set_state(AddCardStates.waiting_for_title)
    
    logger.info(f"User {message.from_user.id} started adding a card")
    
    await message.answer(
        "📝 <b>Создание карточки товара</b>\n\n"
        "Шаг 1/4: Введите название товара:",
        parse_mode="HTML",
        reply_markup=remove_keyboard
    )


@router.message(AddCardStates.waiting_for_title)
async def add_card_title(message: Message, state: FSMContext):
    if not message.text or len(message.text) > 255:
        await message.answer("❌ Название должно содержать от 1 до 255 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(title=message.text)
    await state.set_state(AddCardStates.waiting_for_description)
    
    await message.answer("📄 Шаг 2/4: Введите описание товара:")


@router.message(AddCardStates.waiting_for_description)
async def add_card_description(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(description=message.text)
    await state.set_state(AddCardStates.waiting_for_price)
    
    await message.answer("💰 Шаг 3/4: Введите цену товара (число):")


@router.message(AddCardStates.waiting_for_price, PriceValidationFilter())
async def add_card_price(message: Message, state: FSMContext):
    price = Decimal(message.text.replace(',', '.'))
    
    await state.update_data(price=price)
    await state.set_state(AddCardStates.waiting_for_photo)
    
    await message.answer(
        "🖼 Шаг 4/4: Отправьте фото товара или нажмите кнопку для пропуска:",
        reply_markup=get_skip_photo_keyboard()
    )


@router.message(AddCardStates.waiting_for_price)
async def add_card_price_invalid(message: Message):
    await message.answer("❌ Введите корректную цену (положительное число):")


@router.message(AddCardStates.waiting_for_photo, F.photo)
async def add_card_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    
    card = await db.add_card(
        user_id=message.from_user.id,
        title=data['title'],
        description=data['description'],
        price=data['price'],
        photo_id=photo_id
    )
    
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    logger.info(f"User {message.from_user.id} created card {card.id} with photo")
    
    await message.answer(
        "✅ <b>Карточка создана!</b>\n\n"
        "Она отправлена на модерацию и скоро будет проверена администратором.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )


@router.message(AddCardStates.waiting_for_photo, F.text == "⏩ Пропустить фото")
async def add_card_skip_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    
    card = await db.add_card(
        user_id=message.from_user.id,
        title=data['title'],
        description=data['description'],
        price=data['price'],
        photo_id=None
    )
    
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    logger.info(f"User {message.from_user.id} created card {card.id} without photo")
    
    await message.answer(
        "✅ <b>Карточка создана!</b>\n\n"
        "Она отправлена на модерацию и скоро будет проверена администратором.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )


@router.message(AddCardStates.waiting_for_photo)
async def add_card_photo_invalid(message: Message):
    await message.answer(
        "❌ Пожалуйста, отправьте фото или нажмите кнопку для пропуска.",
        reply_markup=get_skip_photo_keyboard()
    )


@router.message(F.text == "📋 Посмотреть карточки")
async def view_cards(message: Message, state: FSMContext):
    await state.clear()
    cards = await db.get_approved_cards()
    
    if not cards:
        await message.answer("📭 Пока нет одобренных карточек.")
        return
    
    await state.update_data(current_card_index=0, card_ids=[card.id for card in cards])
    
    card = cards[0]
    await send_card(message, card, 0, len(cards))
    
    logger.info(f"User {message.from_user.id} viewing cards")


async def send_card(message: Message, card, index: int, total: int):
    text = (
        f"<b>{card.title}</b>\n\n"
        f"{card.description}\n\n"
        f"💰 Цена: <b>{card.price:.2f}</b> руб."
    )
    
    keyboard = get_cards_navigation_keyboard(index, total, card.id)
    
    if card.photo_id:
        await message.answer_photo(
            photo=card.photo_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("card_prev:"))
async def card_previous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_ids = data.get('card_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index - 1
    
    if new_index < 0:
        await callback.answer("Это первая карточка")
        return
    
    card = await db.get_card(card_ids[new_index])
    
    if card:
        await state.update_data(current_card_index=new_index)
        
        text = (
            f"<b>{card.title}</b>\n\n"
            f"{card.description}\n\n"
            f"💰 Цена: <b>{card.price:.2f}</b> руб."
        )
        
        keyboard = get_cards_navigation_keyboard(new_index, len(card_ids), card.id)
        
        try:
            if card.photo_id:
                await callback.message.edit_caption(
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        except:
            pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("card_next:"))
async def card_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_ids = data.get('card_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index + 1
    
    if new_index >= len(card_ids):
        await callback.answer("Это последняя карточка")
        return
    
    card = await db.get_card(card_ids[new_index])
    
    if card:
        await state.update_data(current_card_index=new_index)
        
        text = (
            f"<b>{card.title}</b>\n\n"
            f"{card.description}\n\n"
            f"💰 Цена: <b>{card.price:.2f}</b> руб."
        )
        
        keyboard = get_cards_navigation_keyboard(new_index, len(card_ids), card.id)
        
        try:
            if card.photo_id:
                await callback.message.edit_caption(
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        except:
            pass
    
    await callback.answer()


@router.callback_query(F.data == "card_count")
async def card_count_callback(callback: CallbackQuery):
    await callback.answer()