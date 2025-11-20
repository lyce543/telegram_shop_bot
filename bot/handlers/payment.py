from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from decimal import Decimal

from bot.database.database import db
from bot.keyboards.reply import get_main_keyboard, remove_keyboard
from bot.filters.custom_filters import IsPrivateFilter, AmountValidationFilter
from bot.states.states import WithdrawalStates
from bot.config import config
from bot.utils.logger import logger

router = Router()
router.message.filter(IsPrivateFilter())


@router.message(F.text == "💰 Баланс")
async def show_balance(message: Message, state: FSMContext):
    await state.clear()
    
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Ошибка получения данных.")
        return
    
    from bot.keyboards.inline import get_balance_keyboard
    
    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"Доступно: <b>{user.balance:.2f}</b> руб.\n\n"
        f"Нажмите кнопку ниже для вывода средств."
    )
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_balance_keyboard()
    )
    
    logger.info(f"User {message.from_user.id} checked balance: {user.balance}")


@router.callback_query(F.data == "withdraw")
async def start_withdrawal(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    user = await db.get_user(callback.from_user.id)
    
    if not user or user.balance <= 0:
        await callback.message.answer("❌ Недостаточно средств для вывода.")
        return
    
    await state.set_state(WithdrawalStates.waiting_for_amount)
    
    await callback.message.answer(
        f"💸 <b>Вывод средств</b>\n\n"
        f"Доступно: <b>{user.balance:.2f}</b> руб.\n\n"
        f"Введите сумму для вывода:",
        parse_mode="HTML",
        reply_markup=remove_keyboard
    )


@router.message(WithdrawalStates.waiting_for_amount, AmountValidationFilter())
async def withdrawal_amount(message: Message, state: FSMContext):
    amount = Decimal(message.text.replace(',', '.'))
    
    user = await db.get_user(message.from_user.id)
    
    if not user or user.balance < amount:
        await message.answer("❌ Недостаточно средств на балансе.")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(WithdrawalStates.waiting_for_requisites)
    
    await message.answer(
        "💳 Введите реквизиты для вывода\n"
        "(номер карты, кошелька и т.д.):"
    )


@router.message(WithdrawalStates.waiting_for_amount)
async def withdrawal_amount_invalid(message: Message):
    await message.answer("❌ Введите корректную сумму (положительное число):")


@router.message(WithdrawalStates.waiting_for_requisites)
async def withdrawal_requisites(message: Message, state: FSMContext):
    if not message.text or len(message.text) < 5:
        await message.answer("❌ Реквизиты должны содержать минимум 5 символов:")
        return
    
    data = await state.get_data()
    amount = data['amount']
    
    withdrawal = await db.create_withdrawal(
        user_id=message.from_user.id,
        amount=amount,
        requisites=message.text
    )
    
    if not withdrawal:
        await message.answer("❌ Ошибка создания заявки на вывод.")
        return
    
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    
    logger.info(f"User {message.from_user.id} created withdrawal request: {amount}")
    
    await message.answer(
        f"✅ <b>Заявка на вывод создана!</b>\n\n"
        f"Сумма: <b>{amount:.2f}</b> руб.\n"
        f"Реквизиты: {message.text}\n\n"
        f"Заявка будет обработана в ближайшее время.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin=is_admin)
    )


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    card_id = int(callback.data.split(':')[1])
    
    card = await db.get_card(card_id)
    
    if not card:
        await callback.answer("❌ Карточка не найдена", show_alert=True)
        return
    
    if card.user_id == callback.from_user.id:
        await callback.answer("❌ Вы не можете купить свой товар", show_alert=True)
        return
    
    if not config.PAYMENT_PROVIDER_TOKEN:
        await callback.answer("❌ Оплата временно недоступна", show_alert=True)
        return
    
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=card.title,
        description=card.description,
        payload=f"card_{card.id}",
        provider_token=config.PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[
            LabeledPrice(label=card.title, amount=int(card.price * 100))
        ]
    )
    
    await callback.answer()
    
    logger.info(f"User {callback.from_user.id} initiated purchase of card {card_id}")


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    card_id = int(payload.split('_')[1])
    amount = Decimal(message.successful_payment.total_amount) / 100
    
    card = await db.get_card(card_id)
    
    if card:
        await db.add_purchase(
            user_id=message.from_user.id,
            card_id=card_id,
            amount=amount,
            seller_id=card.user_id
        )
        
        logger.info(f"User {message.from_user.id} successfully purchased card {card_id} for {amount}")
        
        await message.answer(
            f"✅ <b>Покупка успешна!</b>\n\n"
            f"Товар: {card.title}\n"
            f"Сумма: {amount:.2f} руб.\n\n"
            f"Спасибо за покупку!",
            parse_mode="HTML"
        )