import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway возьмёт токен отсюда
BENEFICIARY_CHAT_ID = 6885214664     # <-- ВСТАВЬ СВОЙ РЕАЛЬНЫЙ TELEGRAM ID
# ===============================================

logging.basicConfig(level=logging.INFO)

ASK_NAME, ASK_ADDRESS = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("☕ Есть кофейный жмых", callback_data="coffee")]
    ]
    await update.message.reply_text(
        "Здравствуйте! Нажмите кнопку, если у вас есть кофейный жмых ♻️",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.clear()
    context.user_data["state"] = ASK_NAME

    await query.message.reply_text("Введите название кофейни:")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    if state == ASK_NAME:
        context.user_data["coffee_name"] = update.message.text
        context.user_data["state"] = ASK_ADDRESS
        await update.message.reply_text("Введите адрес кофейни:")
        return

    if state == ASK_ADDRESS:
        coffee_name = context.user_data.get("coffee_name")
        address = update.message.text

        text = (
            "☕ *Новый кофейный жмых!*\n\n"
            f"🏪 Кофейня: {coffee_name}\n"
            f"📍 Адрес: {address}"
        )

        await context.bot.send_message(
            chat_id=BENEFICIARY_CHAT_ID,
            text=text,
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            "✅ Спасибо! Мы уведомили бенефициара. Он скоро приедет 🚚♻️"
        )

        context.user_data.clear()


def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN не найден. Проверь Variables в Railway.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("🤖 EcoBrew Bot запущен и работает 24/7")
    app.run_polling()


if __name__ == "__main__":
    main()


