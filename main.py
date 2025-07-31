import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Text
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class OrderStates(StatesGroup):
    waiting_for_direction = State()
    waiting_for_location = State()
    waiting_for_contact = State()

@dp.message(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    text = (
        "🚖 ШЫМБАЙ-НУКУС ТАКСИ 🚖\n\n"
        "📍 БИЗДИҢ МАРШРУТЛАРЫМЫЗ\n\n"
        "↗️ ШЫМБАЙДАН ➡️ НӨКИСГЕ\n"
        "↙️ НӨКИСТЕН ⬅️ ШЫМБАЙҒА\n\n"
        "🚖 Басқа қалаларға да хызмет көрсетемиз:\n"
        "• ТЕК ҒАНА БУЫРТПА АРҚАЛЫ\n\n"
        "📞 +998770149797\n"
        "📞 +998770149797\n\n"
        "👨‍💻 АДМИН: @rakhim753\n\n"
        "Төмендеги кнопкалардын өзиңизге кереклисин таңлаң! 😊"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="🚗 ШЫМБАЙ ➡️ НӨКИС", callback_data="direction:shymbay_nukus")
    kb.button(text="🚕 НӨКИС ➡️ ШЫМБАЙ", callback_data="direction:nukus_shymbay")
    kb.adjust(1)
    await state.clear()
    await message.answer(text, reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("direction:"))
async def direction_chosen(callback: types.CallbackQuery, state: FSMContext):
    direction = callback.data.split(":", 1)[1]
    await state.update_data(direction=direction)
    loc_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Орналасқан орнымды жіберу", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await state.set_state(OrderStates.waiting_for_location)
    await callback.message.answer("📍 Орналасқан жеріңізді жіберіңіз:", reply_markup=loc_kb)
    await callback.answer()

@dp.message(OrderStates.waiting_for_location, F.location)
async def got_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.location)
    contact_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Телефон нөмірімді жіберу", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await state.set_state(OrderStates.waiting_for_contact)
    await message.answer("📞 Енді телефон нөміріңізді жіберіңіз:", reply_markup=contact_kb)

@dp.message(OrderStates.waiting_for_contact, F.contact)
async def got_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    direction = data.get("direction", "Белгісіз")
    location = data.get("location")
    contact = message.contact

    direction_text = "ШЫМБАЙ ➡️ НӨКИС" if direction == "shymbay_nukus" else "НӨКИС ➡️ ШЫМБАЙ"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    order_text = (
        "📥 Жаңа тапсырыс!\n\n"
        f"📌 Бағыты: {direction_text}\n"
        f"👤 Аты: {message.from_user.full_name}\n"
        f"📞 Нөмірі: {contact.phone_number}\n"
        f"📍 Локация: https://maps.google.com/?q={location.latitude},{location.longitude}\n"
        f"🕒 Уақыты: {timestamp}"
    )

    await bot.send_message(chat_id=ADMIN_ID, text=order_text)
    await message.answer("✅ Тапсырысыңыз қабылданды!", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.message(OrderStates.waiting_for_contact)
async def need_contact(message: types.Message):
    await message.answer("📞 Төмендегі батырма арқылы нөміріңізді жіберіңіз.")

@dp.message(OrderStates.waiting_for_location)
async def need_location(message: types.Message):
    await message.answer("📍 Локацияны жіберу үшін батырманы басыңыз.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))