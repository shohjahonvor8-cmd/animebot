from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Anime qo‘shish")],
        [KeyboardButton(text="🎬 Anime qismlari")],
        [KeyboardButton(text="📢 Reklama yuborish")],
        [KeyboardButton(text="📺 Kanal qo‘shish")]
    ],
    resize_keyboard=True
)


user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Anime ko‘rish")]
    ],
    resize_keyboard=True
)