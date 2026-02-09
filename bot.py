import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BENEFICIARY_CHAT_ID = 5284035173  # <-- твой Telegram ID

logging.basicConfig(level=logging.INFO)

WAIT_LOCATION = 1


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("☕ Есть кофейный жмых", callback_data="coffee")]
    ]
    await update.message.reply_text(
        "Нажмите кнопку ниже 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------- КНОПКА «ЕСТЬ КОФЕ» ----------
async def coffee_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["state"] = WAIT_LOCATION

    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await query.message.reply_text(
        "Отправьте геолокацию кофейни 📍",
        reply_markup=location_keyboard
    )


# ---------- ПОЛУЧЕНИЕ ГЕОЛОКАЦИИ ----------
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") != WAIT_LOCATION:
        return

    location = update.message.location
    lat = location.latitude
    lon = location.longitude

    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    # Кнопка «Забрал» для бенефициара
    beneficiary_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Забрал", callback_data="picked")]]
    )

    sent = await context.bot.send_message(
        chat_id=BENEFICIARY_CHAT_ID,
        text=f"☕ Новый кофейный жмых\n📍 {maps_link}",
        reply_markup=beneficiary_keyboard
    )

    # Сохраняем ID сообщения бенефициара
    context.bot_data[sent.message_id] = sent.message_id

    await update.message.reply_text(
        "✅ Заявка отправлена",
        reply_markup=ReplyKeyboardMarkup([[]], remove_keyboard=True)
    )

    context.user_data.clear()


# ---------- КНОПКА «ЗАБРАЛ» ----------
async def picked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    message_id = query.message.message_id
    chat_id = query.message.chat_id

    # Удаляем сообщение
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(coffee_button, pattern="^coffee$"))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CallbackQueryHandler(picked_handler, pattern="^picked$"))

    print("🤖 EcoBrew Bot (геолокация + забрал)")
    app.run_polling()


if __name__ == "__main__":
    main()
