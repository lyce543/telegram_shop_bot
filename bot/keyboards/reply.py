from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="➕ Добавить карточку"),
        KeyboardButton(text="📋 Посмотреть карточки")
    )
    builder.row(KeyboardButton(text="💰 Баланс"))
    
    if is_admin:
        builder.row(KeyboardButton(text="👨‍💼 Админ меню"))
    
    return builder.as_markup(resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="✅ Модерация"),
        KeyboardButton(text="📊 Статистика")
    )
    builder.row(KeyboardButton(text="💸 Заявки на вывод"))
    builder.row(KeyboardButton(text="◀️ Назад"))
    
    return builder.as_markup(resize_keyboard=True)


def get_skip_photo_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="⏩ Пропустить фото"))
    return builder.as_markup(resize_keyboard=True)


def get_edit_field_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📝 Название"),
        KeyboardButton(text="📄 Описание")
    )
    builder.row(
        KeyboardButton(text="💰 Цена"),
        KeyboardButton(text="🖼 Фото")
    )
    builder.row(KeyboardButton(text="❌ Отмена"))
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


remove_keyboard = ReplyKeyboardRemove()