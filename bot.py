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

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👥 СПИСОК БЕНЕФИЦИАРОВ
BENEFICIARY_CHAT_IDS = [
    5284035173,   # бенефициар 1
    6885214664,
    6170555228,   # бенефициар 2 (если появится)
]
# ============================================

logging.basicConfig(level=logging.INFO)

WAIT_COFFEE = 1
WAIT_LOCATION = 2

# Храним message_id заявок: request_id -> [(chat_id, message_id)]
active_requests = {}


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
        "Нажмите ☕ и отправьте геолокацию 📍",
        reply_markup=main_keyboard()
    )


# ---------- КНОПКА ☕ ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "☕ Есть кофейный жмых":
        context.user_data["state"] = WAIT_LOCATION
        await update.message.reply_text(
            "Теперь отправьте геолокацию 📍",
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

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ Забрал", callback_data="picked")]]
    )

    request_id = f"{update.message.from_user.id}_{update.message.message_id}"
    active_requests[request_id] = []

    for chat_id in BENEFICIARY_CHAT_IDS:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"☕ Новый кофейный жмых\n📍 {maps_link}",
            reply_markup=keyboard
        )
        active_requests[request_id].append((chat_id, msg.message_id))

    await update.message.reply_text(
        "✅ Заявка отправлена",
        reply_markup=ReplyKeyboardMarkup([], remove_keyboard=True)
    )

    context.user_data.clear()


# ---------- КНОПКА «ЗАБРАЛ» ----------
async def picked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    message_id = query.message.message_id
    chat_id = query.message.chat_id

    # Ищем заявку
    for request_id, messages in list(active_requests.items()):
        if (chat_id, message_id) in messages:
            # Удаляем у ВСЕХ бенефициаров
            for cid, mid in messages:
                try:
                    await context.bot.delete_message(chat_id=cid, message_id=mid)
                except:
                    pass
            del active_requests[request_id]
            break


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не найден")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CallbackQueryHandler(picked_handler, pattern="^picked$"))

    print("🤖 EcoBrew Bot (несколько бенефициаров)")
    app.run_polling()


if __name__ == "__main__":
    main()

