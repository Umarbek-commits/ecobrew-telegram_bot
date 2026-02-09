import logging
import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
BENEFICIARY_CHAT_ID = 5284035173  # <-- ТВОЙ ID

logging.basicConfig(level=logging.INFO)

WAIT_COFFEE = 1
WAIT_LOCATION = 2


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["☕ Есть кофейный жмых"],
            [KeyboardButton("📍 Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True
    )


# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["state"] = WAIT_COFFEE
    await update.message.reply_text(
        "Нажмите кнопку ☕, затем отправьте геолокацию 📍",
        reply_markup=main_keyboard()
    )


# ---------- ТЕКСТОВЫЕ КНОПКИ ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    state = context.user_data.get("state")

    if text == "☕ Есть кофейный жмых" and state == WAIT_COFFEE:
        context.user_data["state"] = WAIT_LOCATION
        await update.message.reply_text(
            "Теперь нажмите 📍 Отправить геолокацию",
            reply_markup=main_keyboard()
        )


# ---------- ГЕОЛОКАЦИЯ ----------
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("state") != WAIT_LOCATION:
        return

    location = update.message.location
    lat = location.latitude
    lon = location.longitude

    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    beneficiary_keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Забрал", callback_data="picked")]]
    )

    await context.bot.send_message(
        chat_id=BENEFICIARY_CHAT_ID,
        text=f"☕ Новый кофейный жмых\n📍 {maps_link}",
        reply_markup=beneficiary_keyboard
    )

    await update.message.reply_text(
        "✅ Заявка отправлена",
        reply_markup=ReplyKeyboardMarkup([], remove_keyboard=True)
    )

    context.user_data.clear()


# ---------- «ЗАБРАЛ» ----------
async def picked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id
    )


def setup_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CallbackQueryHandler(picked_handler, pattern="^picked$"))

    print("🤖 EcoBrew Bot (две кнопки снизу)")
    return app


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    setup_app().run_polling()
