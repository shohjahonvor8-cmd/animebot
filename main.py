import asyncio
import logging
from keyboards import admin_menu, user_menu
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from state import AnimeAdd,EpisodeAdd,Broadcast,AddChannel
from db import conn, cursor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

BOT_TOKEN = "8632070353:AAGmIpTT-ti-nro89PQIRBCVkz5znjVgc1I"
ADMIN_ID = 5848239501

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)

# 🔥 FIX: FSM storage qo‘shildi
dp = Dispatcher(storage=MemoryStorage())
router = Router()
@router.message(F.text == "/start")
async def start_handler(message: Message):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (str(message.from_user.id),)
    )
    conn.commit()

    # admin
    if message.from_user.id == ADMIN_ID:
        await message.answer("🔐 Admin panel", reply_markup=admin_menu)
        return

    # channel olish
    cursor.execute("SELECT link FROM channels ORDER BY id DESC LIMIT 1")
    channel = cursor.fetchone()

    if not channel:
        await message.answer("❌ Kanal topilmadi")
        return

    channel_username = "@" + channel[0].replace("@", "")

    try:
        member = await bot.get_chat_member(channel_username, message.from_user.id)

        # ✅ AGAR OBUNA BO'LGAN BO'LSA
        if member.status in ["member", "administrator", "creator"]:
            await message.answer("🎬 Anime kodini yuboring 👇")
            return

    except:
        pass

    # ❌ OBUNA BO'LMAGANLARGA FAQAT SHU CHIQADI
    raw_link = channel[0].replace("@", "")
    url = f"https://t.me/{raw_link}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Obuna bo‘lish", url=url)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

    await message.answer("📢 Avval kanalga obuna bo‘ling:", reply_markup=keyboard)


@router.message(F.text == "➕ Anime qo‘shish")
async def add_anime(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("🎬 Anime nomini yozing:")
    await state.set_state(AnimeAdd.name)


@router.message(AnimeAdd.name)
async def anime_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer("🔑 Anime kodi (unique) yozing:")
    await state.set_state(AnimeAdd.code)


@router.message(AnimeAdd.code)
async def anime_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.lower().strip())

    await message.answer("🎞 Episode sonini yozing:")
    await state.set_state(AnimeAdd.episodes)


@router.message(AnimeAdd.episodes)
async def anime_episodes(message: Message, state: FSMContext):
    await state.update_data(episodes=message.text)

    await message.answer("📺 Video yuboring:")
    await state.set_state(AnimeAdd.video)


@router.message(AnimeAdd.video)
async def anime_video(message: Message, state: FSMContext):
    data = await state.get_data()

    name = data["name"]
    code = data["code"]
    episodes = data["episodes"]

    # 🔥 FIX: video + text
    if not message.video:
        await message.answer("❌ Faqat VIDEO yuboring!")
        return

    video = message.video.file_id

    cursor.execute("""
        INSERT INTO animes (name, code, episodes, video)
        VALUES (?, ?, ?, ?)
    """, (name, code, episodes, video))

    conn.commit()

    await message.answer(
        f"✅ Anime saqlandi!\n\n"
        f"🎬 {name}\n"
        f"🔑 {code}\n"
        f"🎞 {episodes}"
    )

    await state.clear()


dp.include_router(router)


@router.message(F.text == "🎬 Anime qismlari")
async def show_animes(message: Message):
    cursor.execute("SELECT id, name FROM animes")
    animes = cursor.fetchall()

    if not animes:
        await message.answer("❌ Anime yo‘q")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"anime_{id}")]
            for id, name in animes
        ]
    )

    await message.answer("🎬 Qaysi animega qism qo‘shamiz?", reply_markup=keyboard)

@router.callback_query(F.data.startswith("anime_"))
async def select_anime(call: CallbackQuery, state: FSMContext):
    anime_id = int(call.data.split("_")[1])

    await state.update_data(anime_id=anime_id)

    await call.message.answer("🎞 Nechinchi qism?")
    await state.set_state(EpisodeAdd.episode_number)

    await call.answer()

@router.message(EpisodeAdd.episode_number)
async def episode_number(message: Message, state: FSMContext):
    await state.update_data(episode_number=message.text)

    await message.answer("📺 Video yuboring:")
    await state.set_state(EpisodeAdd.video)

@router.message(EpisodeAdd.video)
async def save_episode(message: Message, state: FSMContext):
    data = await state.get_data()

    anime_id = data["anime_id"]
    episode_number = data["episode_number"]

    # video tekshiruv
    if not message.video:
        await message.answer("❌ Video yuboring!")
        return

    video = message.video.file_id

    # 🔥 DB ga saqlash (FIXED)
    cursor.execute("""
        INSERT INTO episodes (anime_id, episode_number, video)
        VALUES (?, ?, ?)
    """, (anime_id, int(episode_number), video))

    conn.commit()

    await message.answer(f"✅ Episode {episode_number} saqlandi!")
    await state.clear()

@router.message(F.text == "📢 Reklama yuborish")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("📸 Video yoki rasm yuboring:")
    await state.set_state(Broadcast.media)

@router.message(Broadcast.media)
async def get_media(message: Message, state: FSMContext):
    media_id = None
    media_type = None

    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = "photo"

    elif message.video:
        media_id = message.video.file_id
        media_type = "video"

    else:
        await message.answer("❌ Faqat rasm yoki video yuboring!")
        return

    await state.update_data(media_id=media_id, media_type=media_type)

    await message.answer("✍️ Endi reklama textini yozing:")
    await state.set_state(Broadcast.text)


@router.message(Broadcast.text)
async def send_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()

    media_id = data["media_id"]
    media_type = data["media_type"]
    text = message.text

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    success = 0

    for user in users:
        try:
            uid = user[0]

            if media_type == "photo":
                await bot.send_photo(uid, photo=media_id, caption=text)

            elif media_type == "video":
                await bot.send_video(uid, video=media_id, caption=text)

            success += 1

        except:
            pass

    await message.answer(f"✅ Reklama yuborildi!\n👤 {success} ta userga")

    await state.clear()
@router.message(F.text == "📺 Kanal qo‘shish")
async def add_channel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer("📎 Kanal linkini yuboring:")
    await state.set_state(AddChannel.link)


@router.message(AddChannel.link)
async def save_channel(message: Message, state: FSMContext):
    link = message.text.strip()

    # ❌ username bo‘lsa
    if link.startswith("@"):
        link = link[1:]

    # ❌ to‘liq link bo‘lsa
    link = link.replace("https://t.me/", "")
    link = link.replace("http://t.me/", "")
    link = link.replace("t.me/", "")

    # ✅ DATABASEGA FAQAT USERNAME SAQLAYMIZ
    cursor.execute("""
        INSERT INTO channels (name, link)
        VALUES (?, ?)
    """, ("Telegram Channel", link))

    conn.commit()

    await message.answer("✅ Kanal saqlandi!")
    await state.clear()


@router.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    cursor.execute("SELECT link FROM channels ORDER BY id DESC LIMIT 1")
    channel = cursor.fetchone()

    if not channel:
        await call.message.answer("❌ Kanal topilmadi")
        return

    channel_username = channel[0]

    # 🔥 FIX: format
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username

    try:
        member = await bot.get_chat_member(channel_username, call.from_user.id)

        if member.status in ["member", "administrator", "creator"]:
            await call.message.answer("🎬 Endi anime kodini yuboring 👇")
        else:
            await call.message.answer("❌ Hali obuna bo‘lmadingiz")

    except Exception as e:
        await call.message.answer(
            "❌ Kanal topilmadi yoki bot admin emas\n\n"
            "👉 Botni kanalga ADMIN qilib qo‘ying"
        )
@router.message(F.text)
async def get_anime_by_code(message: Message):
    code = message.text.lower().strip()

    # /start va commandlarni bloklash
    if code.startswith("/"):
        return

    cursor.execute("""
        SELECT id, name, code, video
        FROM animes
        WHERE code = ?
    """, (code,))

    anime = cursor.fetchone()

    if not anime:
        await message.answer("❌ Bunday kodli anime topilmadi")
        return

    anime_id, name, code, video = anime

    # episodes olish
    cursor.execute("""
        SELECT episode_number
        FROM episodes
        WHERE anime_id = ?
        ORDER BY episode_number ASC
    """, (anime_id,))

    eps = cursor.fetchall()

    # ❌ EPISODE YO‘Q HOLAT
    if not eps:
        await message.answer("❌ Episode yo‘q")
        return

    # ================= INLINE BUTTONS (6 tadan) =================
    buttons = []
    row = []

    for i, ep in enumerate(eps, start=1):
        row.append(
            InlineKeyboardButton(
                text=f"🎬{ep[0]}",
                callback_data=f"ep_{anime_id}_{ep[0]}"
            )
        )

        # har 6 ta tugma = yangi qator
        if i % 6 == 0:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer_video(
        video=video,
        caption=f"🎬 {name}\n🔑 Code: {code}",
        reply_markup=keyboard
    )


# ================= EPISODE SEND =================
@router.callback_query(F.data.startswith("ep_"))
async def send_episode(call: CallbackQuery):
    _, anime_id, ep_num = call.data.split("_")

    anime_id = int(anime_id)
    ep_num = int(ep_num)

    cursor.execute("""
        SELECT video
        FROM episodes
        WHERE anime_id = ? AND episode_number = ?
    """, (anime_id, ep_num))

    data = cursor.fetchone()

    if not data:
        await call.message.answer("❌ Episode topilmadi")
        return

    await call.message.answer_video(
        video=data[0],
        caption=f"🎬 Episode {ep_num}"
    )

    await call.answer()

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())