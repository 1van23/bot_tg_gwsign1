import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN, CHANNEL_USERNAME
from asyncio import sleep
from collections import defaultdict

# Хранилище тех, кто "в ожидании"
waiting_users = defaultdict(lambda: False)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Кнопки
def get_subscribe_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подписался", callback_data="check_sub")
    return kb.as_markup()


def get_price_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="📄 Получить прайс", callback_data="get_price")
    return kb.as_markup()


def get_bonus_button():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Бонус", callback_data="get_bonus")
    return kb.as_markup()


# Проверка подписки
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False


async def wait_and_remind(user_id: int):
    await sleep(600)  # 10 минут

    if waiting_users.get(user_id):
        try:
            await bot.send_message(
                user_id,
                "Я жду уже 10 минут, нажми на кнопку и получи прайс 😅",
                reply_markup=get_subscribe_button()
            )
        except Exception as e:
            print(f"Не удалось отправить напоминание: {e}")


# Старт
@dp.message(F.text, F.text.lower() == "/start")
async def start(message: types.Message):
    user_id = message.from_user.id

    if await is_subscribed(user_id):
        await message.answer(
            "Нажми кнопку ниже, чтобы получить прайс:",
            reply_markup=get_price_button()
        )
    else:
        await message.answer(
            "Привет! Чтобы получить прайс, сначала подпишись на наш канал:",
            reply_markup=get_subscribe_button()
        )
        await message.answer(CHANNEL_USERNAME)

        # Помечаем, что пользователь ожидается
        waiting_users[user_id] = True
        asyncio.create_task(wait_and_remind(user_id))


# Обработка кнопки "Я подписался"
@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    waiting_users[callback.from_user.id] = False
    if await is_subscribed(user_id):
        await callback.message.answer(
            "Жми кнопку ниже и получай актуальный прайс на кастомные дорожные знаки👇",
            reply_markup=get_price_button()
        )
    else:
        await callback.message.answer(
            "Меня не обмануть! Сначала подпишись на канал,чтобы я мог отправить прайс.",
            reply_markup=get_subscribe_button()
        )
    await callback.answer()


# Обработка кнопки "прайс"
@dp.callback_query(F.data == "get_price")
async def send_price(callback: types.CallbackQuery):
    pdf_file = FSInputFile("files/price.pdf")
    await callback.message.answer_document(
        document=pdf_file,
        caption="Отправляю тебе pdf файл с актуальными ценами. Также оставлю здесь кнопку, нажми, если хочешь💼",
        reply_markup=get_bonus_button()
    )
    await callback.answer()


# Обработка кнопки "бонус"
@dp.callback_query(F.data == "get_bonus")
async def send_bonus(callback: types.CallbackQuery):
    video_file = FSInputFile("files/bonus.mp4")
    await callback.message.answer_video(
        video=video_file,
        caption="Досмотри видео до конца, чтобы получить бонус лично от меня! Создать индивидуальный дизайн для своего знака или сделать заказ на один из тех, который уже видел у меня, можно здесь @GWSign_Bot 🎉"
    )
    await callback.answer()


# Запуск
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
