from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.database.database import db
from bot.database.models import ModerationStatus
from bot.keyboards.reply import (
    get_admin_keyboard, 
    get_main_keyboard, 
    get_edit_field_keyboard,
    remove_keyboard
)
from bot.keyboards.inline import get_moderation_keyboard, get_withdrawals_keyboard
from bot.filters.custom_filters import IsAdminFilter, IsPrivateFilter
from bot.states.states import EditCardStates
from bot.config import config
from bot.utils.logger import logger

router = Router()
router.message.filter(IsPrivateFilter(), IsAdminFilter())


@router.message(F.text == "👨‍💼 Админ меню")
async def admin_menu(message: Message, state: FSMContext):
    await state.clear()
    
    logger.info(f"Admin {message.from_user.id} opened admin menu")
    
    await message.answer(
        "👨‍💼 <b>Панель администратора</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    
    await message.answer(
        "↩️ Возвращаемся в главное меню",
        reply_markup=get_main_keyboard(is_admin=True)
    )


@router.message(F.text == "✅ Модерация")
async def moderation_menu(message: Message, state: FSMContext):
    await state.clear()
    cards = await db.get_pending_cards()
    
    if not cards:
        await message.answer(
            "✅ Нет карточек на модерации!",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await state.update_data(
        moderation_card_index=0, 
        moderation_card_ids=[card.id for card in cards]
    )
    
    card = cards[0]
    await send_moderation_card(message, card, 0, len(cards))
    
    logger.info(f"Admin {message.from_user.id} started moderation")


async def send_moderation_card(message: Message, card, index: int, total: int):
    user = await db.get_user(card.user_id)
    username = f"@{user.username}" if user.username else user.first_name
    text = (
        f"<b>Модерация карточки #{card.id}</b>\n\n"
        f"👤 Автор: {username} (ID: {card.user_id})\n"
        f"📅 Создана: {card.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Название:</b> {card.title}\n\n"
        f"<b>Описание:</b>\n{card.description}\n\n"
        f"💰 <b>Цена:</b> {card.price:.2f} руб."
    )
    
    keyboard = get_moderation_keyboard(card.id, index, total)
    
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


@router.callback_query(F.data.startswith("moderate_approve:"))
async def moderate_approve(callback: CallbackQuery, state: FSMContext):
    card_id = int(callback.data.split(':')[1])
    
    card = await db.update_card_status(card_id, ModerationStatus.APPROVED)
    
    if card:
        logger.info(f"Admin {callback.from_user.id} approved card {card_id}")
        await callback.answer("✅ Карточка одобрена!", show_alert=True)
        
        data = await state.get_data()
        card_ids = data.get('moderation_card_ids', [])
        current_index = data.get('moderation_card_index', 0)
        
        if card_id in card_ids:
            card_ids.remove(card_id)
            await state.update_data(moderation_card_ids=card_ids)
        
        if not card_ids:
            await callback.message.delete()
            await callback.message.answer(
                "✅ Все карточки проверены!",
                reply_markup=get_admin_keyboard()
            )
            return
        
        next_index = min(current_index, len(card_ids) - 1)
        next_card = await db.get_card(card_ids[next_index])
        
        if next_card and next_card.status == ModerationStatus.PENDING:
            await state.update_data(moderation_card_index=next_index)
            
            user = await db.get_user(next_card.user_id)
            username = f"@{user.username}" if user.username else user.first_name
            
            text = (
                f"<b>Модерация карточки #{next_card.id}</b>\n\n"
                f"👤 Автор: {username} (ID: {next_card.user_id})\n"
                f"📅 Создана: {next_card.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"<b>Название:</b> {next_card.title}\n\n"
                f"<b>Описание:</b>\n{next_card.description}\n\n"
                f"💰 <b>Цена:</b> {next_card.price:.2f} руб."
            )
            
            keyboard = get_moderation_keyboard(next_card.id, next_index, len(card_ids))
            
            try:
                if next_card.photo_id:
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
                await callback.message.delete()
                if next_card.photo_id:
                    await callback.message.answer_photo(
                        photo=next_card.photo_id,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.answer(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )


@router.callback_query(F.data.startswith("moderate_reject:"))
async def moderate_reject(callback: CallbackQuery, state: FSMContext):
    card_id = int(callback.data.split(':')[1])
    
    card = await db.update_card_status(card_id, ModerationStatus.REJECTED)
    
    if card:
        logger.info(f"Admin {callback.from_user.id} rejected card {card_id}")
        await callback.answer("❌ Карточка отклонена!", show_alert=True)
        
        data = await state.get_data()
        card_ids = data.get('moderation_card_ids', [])
        current_index = data.get('moderation_card_index', 0)
        
        if card_id in card_ids:
            card_ids.remove(card_id)
            await state.update_data(moderation_card_ids=card_ids)
        
        if not card_ids:
            await callback.message.delete()
            await callback.message.answer(
                "✅ Все карточки проверены!",
                reply_markup=get_admin_keyboard()
            )
            return
        
        next_index = min(current_index, len(card_ids) - 1)
        next_card = await db.get_card(card_ids[next_index])
        
        if next_card and next_card.status == ModerationStatus.PENDING:
            await state.update_data(moderation_card_index=next_index)
            
            user = await db.get_user(next_card.user_id)
            username = f"@{user.username}" if user.username else user.first_name
            
            text = (
                f"<b>Модерация карточки #{next_card.id}</b>\n\n"
                f"👤 Автор: {username} (ID: {next_card.user_id})\n"
                f"📅 Создана: {next_card.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"<b>Название:</b> {next_card.title}\n\n"
                f"<b>Описание:</b>\n{next_card.description}\n\n"
                f"💰 <b>Цена:</b> {next_card.price:.2f} руб."
            )
            
            keyboard = get_moderation_keyboard(next_card.id, next_index, len(card_ids))
            
            try:
                if next_card.photo_id:
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
                await callback.message.delete()
                if next_card.photo_id:
                    await callback.message.answer_photo(
                        photo=next_card.photo_id,
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.answer(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )


@router.callback_query(F.data.startswith("moderate_edit:"))
async def moderate_edit(callback: CallbackQuery, state: FSMContext):
    card_id = int(callback.data.split(':')[1])
    
    await state.update_data(editing_card_id=card_id)
    await state.set_state(EditCardStates.waiting_for_field_choice)
    
    await callback.message.answer(
        "✏️ <b>Редактирование карточки</b>\n\n"
        "Выберите поле для изменения:",
        parse_mode="HTML",
        reply_markup=get_edit_field_keyboard()
    )
    
    await callback.answer()


@router.message(EditCardStates.waiting_for_field_choice, F.text.in_(["📝 Название", "📄 Описание", "💰 Цена", "🖼 Фото"]))
async def edit_field_choice(message: Message, state: FSMContext):
    field_map = {
        "📝 Название": ("title", "название"),
        "📄 Описание": ("description", "описание"),
        "💰 Цена": ("price", "цену"),
        "🖼 Фото": ("photo_id", "фото")
    }
    
    field_name, field_text = field_map[message.text]
    await state.update_data(editing_field=field_name)
    await state.set_state(EditCardStates.waiting_for_new_value)
    
    await message.answer(
        f"✏️ Введите новое значение для поля <b>{field_text}</b>:",
        parse_mode="HTML",
        reply_markup=remove_keyboard
    )


@router.message(EditCardStates.waiting_for_new_value)
async def edit_new_value(message: Message, state: FSMContext):
    from decimal import Decimal
    
    data = await state.get_data()
    card_id = data.get('editing_card_id')
    field = data.get('editing_field')
    
    if field == "price":
        try:
            new_value = Decimal(message.text.replace(',', '.'))
            if new_value <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Введите корректную цену (положительное число):")
            return
    elif field == "photo_id":
        if message.photo:
            new_value = message.photo[-1].file_id
        else:
            await message.answer("❌ Пожалуйста, отправьте фото:")
            return
    else:
        new_value = message.text
        
        if field == "title" and len(new_value) > 255:
            await message.answer("❌ Название должно содержать не более 255 символов:")
            return
        elif field == "description" and len(new_value) < 10:
            await message.answer("❌ Описание должно содержать минимум 10 символов:")
            return
    
    card = await db.update_card_field(card_id, field, new_value)
    
    if card:
        await state.clear()
        
        logger.info(f"Admin {message.from_user.id} edited card {card_id} field {field}")
        
        await message.answer(
            "✅ Поле успешно обновлено!",
            reply_markup=get_admin_keyboard()
        )


@router.message(EditCardStates.waiting_for_field_choice)
async def edit_field_choice_invalid(message: Message):
    await message.answer(
        "❌ Пожалуйста, выберите поле из предложенных кнопок:",
        reply_markup=get_edit_field_keyboard()
    )


@router.callback_query(F.data.startswith("moderate_prev:"))
async def moderate_previous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_ids = data.get('moderation_card_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index - 1
    
    if new_index < 0:
        await callback.answer("Это первая карточка")
        return
    
    card = await db.get_card(card_ids[new_index])
    
    if card:
        await state.update_data(moderation_card_index=new_index)
        
        user = await db.get_user(card.user_id)
        username = f"@{user.username}" if user.username else user.first_name
        
        text = (
            f"<b>Модерация карточки #{card.id}</b>\n\n"
            f"👤 Автор: {username} (ID: {card.user_id})\n"
            f"📅 Создана: {card.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"<b>Название:</b> {card.title}\n\n"
            f"<b>Описание:</b>\n{card.description}\n\n"
            f"💰 <b>Цена:</b> {card.price:.2f} руб."
        )
        
        keyboard = get_moderation_keyboard(card.id, new_index, len(card_ids))
        
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


@router.callback_query(F.data.startswith("moderate_next:"))
async def moderate_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    card_ids = data.get('moderation_card_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index + 1
    
    if new_index >= len(card_ids):
        await callback.answer("Это последняя карточка")
        return
    
    card = await db.get_card(card_ids[new_index])
    
    if card:
        await state.update_data(moderation_card_index=new_index)
        
        user = await db.get_user(card.user_id)
        username = f"@{user.username}" if user.username else user.first_name
        
        text = (
            f"<b>Модерация карточки #{card.id}</b>\n\n"
            f"👤 Автор: {username} (ID: {card.user_id})\n"
            f"📅 Создана: {card.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"<b>Название:</b> {card.title}\n\n"
            f"<b>Описание:</b>\n{card.description}\n\n"
            f"💰 <b>Цена:</b> {card.price:.2f} руб."
        )
        
        keyboard = get_moderation_keyboard(card.id, new_index, len(card_ids))
        
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


@router.callback_query(F.data == "moderate_count")
async def moderate_count_callback(callback: CallbackQuery):
    await callback.answer()


@router.message(F.text == "📊 Статистика")
async def statistics_menu(message: Message):
    stats = await db.get_user_statistics()
    
    if not stats:
        await message.answer("📊 Пока нет статистики")
        return
    
    text = "📊 <b>Статистика пользователей</b>\n\n"
    
    for stat in stats:
        username = f"@{stat['username']}" if stat['username'] else stat['first_name']
        text += (
            f"👤 {username} (ID: {stat['user_id']})\n"
            f"   📦 Всего карточек: {stat['total_cards']}\n"
            f"   ✅ Одобрено: {stat['approved']}\n"
            f"   ❌ Отклонено: {stat['rejected']}\n\n"
        )
    
    logger.info(f"Admin {message.from_user.id} viewed statistics")
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💸 Заявки на вывод")
async def withdrawals_menu(message: Message, state: FSMContext):
    await state.clear()
    withdrawals = await db.get_pending_withdrawals()
    
    if not withdrawals:
        await message.answer(
            "✅ Нет заявок на вывод!",
            reply_markup=get_admin_keyboard()
        )
        return
    
    await state.update_data(
        withdrawal_index=0,
        withdrawal_ids=[w.id for w in withdrawals]
    )
    
    withdrawal = withdrawals[0]
    await send_withdrawal(message, withdrawal, 0, len(withdrawals))
    
    logger.info(f"Admin {message.from_user.id} opened withdrawals")


async def send_withdrawal(message: Message, withdrawal, index: int, total: int):
    user = await db.get_user(withdrawal.user_id)
    username = f"@{user.username}" if user.username else user.first_name
    
    text = (
        f"<b>Заявка на вывод #{withdrawal.id}</b>\n\n"
        f"👤 Пользователь: {username} (ID: {withdrawal.user_id})\n"
        f"💰 Сумма: <b>{withdrawal.amount:.2f}</b> руб.\n"
        f"📅 Создана: {withdrawal.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>Реквизиты:</b>\n{withdrawal.requisites}"
    )
    
    keyboard = get_withdrawals_keyboard(withdrawal.id, index, total)
    
    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("withdrawal_complete:"))
async def complete_withdrawal(callback: CallbackQuery, state: FSMContext):
    withdrawal_id = int(callback.data.split(':')[1])
    
    withdrawal = await db.complete_withdrawal(withdrawal_id)
    
    if withdrawal:
        logger.info(f"Admin {callback.from_user.id} completed withdrawal {withdrawal_id}")
        await callback.answer("✅ Выплата проведена!", show_alert=True)
        
        data = await state.get_data()
        withdrawal_ids = data.get('withdrawal_ids', [])
        current_index = data.get('withdrawal_index', 0)
        
        if withdrawal_id in withdrawal_ids:
            withdrawal_ids.remove(withdrawal_id)
            await state.update_data(withdrawal_ids=withdrawal_ids)
        
        if not withdrawal_ids:
            await callback.message.delete()
            await callback.message.answer(
                "✅ Все заявки обработаны!",
                reply_markup=get_admin_keyboard()
            )
            return
        
        next_index = min(current_index, len(withdrawal_ids) - 1)
        next_withdrawal = await db.get_pending_withdrawals()
        
        if next_withdrawal:
            next_w = next((w for w in next_withdrawal if w.id == withdrawal_ids[next_index]), None)
            if next_w:
                await state.update_data(withdrawal_index=next_index)
                
                user = await db.get_user(next_w.user_id)
                username = f"@{user.username}" if user.username else user.first_name
                
                text = (
                    f"<b>Заявка на вывод #{next_w.id}</b>\n\n"
                    f"👤 Пользователь: {username} (ID: {next_w.user_id})\n"
                    f"💰 Сумма: <b>{next_w.amount:.2f}</b> руб.\n"
                    f"📅 Создана: {next_w.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"<b>Реквизиты:</b>\n{next_w.requisites}"
                )
                
                keyboard = get_withdrawals_keyboard(next_w.id, next_index, len(withdrawal_ids))
                
                try:
                    await callback.message.edit_text(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                except:
                    await callback.message.delete()
                    await callback.message.answer(
                        text=text,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )


@router.callback_query(F.data.startswith("withdrawal_prev:"))
async def withdrawal_previous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    withdrawal_ids = data.get('withdrawal_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index - 1
    
    if new_index < 0:
        await callback.answer("Это первая заявка")
        return
    
    withdrawals = await db.get_pending_withdrawals()
    withdrawal = next((w for w in withdrawals if w.id == withdrawal_ids[new_index]), None)
    
    if withdrawal:
        await state.update_data(withdrawal_index=new_index)
        
        user = await db.get_user(withdrawal.user_id)
        username = f"@{user.username}" if user.username else user.first_name
        
        text = (
            f"<b>Заявка на вывод #{withdrawal.id}</b>\n\n"
            f"👤 Пользователь: {username} (ID: {withdrawal.user_id})\n"
            f"💰 Сумма: <b>{withdrawal.amount:.2f}</b> руб.\n"
            f"📅 Создана: {withdrawal.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"<b>Реквизиты:</b>\n{withdrawal.requisites}"
        )
        
        keyboard = get_withdrawals_keyboard(withdrawal.id, new_index, len(withdrawal_ids))
        
        try:
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            pass
    
    await callback.answer()


@router.callback_query(F.data.startswith("withdrawal_next:"))
async def withdrawal_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    withdrawal_ids = data.get('withdrawal_ids', [])
    current_index = int(callback.data.split(':')[1])
    
    new_index = current_index + 1
    
    if new_index >= len(withdrawal_ids):
        await callback.answer("Это последняя заявка")
        return
    
    withdrawals = await db.get_pending_withdrawals()
    withdrawal = next((w for w in withdrawals if w.id == withdrawal_ids[new_index]), None)
    
    if withdrawal:
        await state.update_data(withdrawal_index=new_index)
        
        user = await db.get_user(withdrawal.user_id)
        username = f"@{user.username}" if user.username else user.first_name
        
        text = (
            f"<b>Заявка на вывод #{withdrawal.id}</b>\n\n"
            f"👤 Пользователь: {username} (ID: {withdrawal.user_id})\n"
            f"💰 Сумма: <b>{withdrawal.amount:.2f}</b> руб.\n"
            f"📅 Создана: {withdrawal.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"<b>Реквизиты:</b>\n{withdrawal.requisites}"
        )
        
        keyboard = get_withdrawals_keyboard(withdrawal.id, new_index, len(withdrawal_ids))
        
        try:
            await callback.message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            pass
    
    await callback.answer()


@router.callback_query(F.data == "withdrawal_count")
async def withdrawal_count_callback(callback: CallbackQuery):
    await callback.answer()