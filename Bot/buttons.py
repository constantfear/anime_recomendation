from aiogram import types

# Кнопки выключены
empty_keyboard = types.ReplyKeyboardRemove()

# Главные кнопки
recs = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton("Не интересно"),
            # types.KeyboardButton("Просмотренно"),
            types.KeyboardButton("Ввести другое аниме"),
            types.KeyboardButton("Отмена")
        ],
    ],
    resize_keyboard=True
)
