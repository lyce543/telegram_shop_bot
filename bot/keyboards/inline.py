from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_cards_navigation_keyboard(current_index: int, total_cards: int, card_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    buttons = []
    
    if current_index > 0:
        buttons.append(InlineKeyboardButton(text="«", callback_data=f"card_prev:{current_index}"))
    
    buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total_cards}", 
        callback_data="card_count"
    ))
    
    if current_index < total_cards - 1:
        buttons.append(InlineKeyboardButton(text="»", callback_data=f"card_next:{current_index}"))
    
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="💳 Купить", callback_data=f"buy:{card_id}"))
    
    return builder.as_markup()


def get_moderation_keyboard(card_id: int, current_index: int, total_cards: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"moderate_approve:{card_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"moderate_reject:{card_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data=f"moderate_edit:{card_id}")
    )
    
    nav_buttons = []
    
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"moderate_prev:{current_index}"))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total_cards}", 
        callback_data="moderate_count"
    ))
    
    if current_index < total_cards - 1:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"moderate_next:{current_index}"))
    
    builder.row(*nav_buttons)
    
    return builder.as_markup()


def get_balance_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💸 Вывести средства", callback_data="withdraw"))
    return builder.as_markup()


def get_withdrawals_keyboard(withdrawal_id: int, current_index: int, total_withdrawals: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Выплата проведена", callback_data=f"withdrawal_complete:{withdrawal_id}")
    )
    
    nav_buttons = []
    
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="«", callback_data=f"withdrawal_prev:{current_index}"))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total_withdrawals}", 
        callback_data="withdrawal_count"
    ))
    
    if current_index < total_withdrawals - 1:
        nav_buttons.append(InlineKeyboardButton(text="»", callback_data=f"withdrawal_next:{current_index}"))
    
    builder.row(*nav_buttons)
    
    return builder.as_markup()


def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()