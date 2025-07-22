from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# Этапы разговора
AMOUNT, DESCRIPTION = range(2)

data = {
    "transactions": [],
    "balance": 0.0,
    "operation": None  # "income" или "expense"
}

keyboard = [
    ["Добавить доход", "Добавить расход"],
    ["Показать баланс", "Показать отчёт"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выбери действие:",
        reply_markup=reply_markup
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Добавить доход":
        data["operation"] = "income"
        await update.message.reply_text("Введите сумму дохода:", reply_markup=ReplyKeyboardRemove())
        return AMOUNT
    elif text == "Добавить расход":
        data["operation"] = "expense"
        await update.message.reply_text("Введите сумму расхода:", reply_markup=ReplyKeyboardRemove())
        return AMOUNT
    elif text == "Показать баланс":
        await update.message.reply_text(f"Текущий баланс: {data['balance']:.2f}₴", reply_markup=reply_markup)
        return ConversationHandler.END
    elif text == "Показать отчёт":
        if not data["transactions"]:
            await update.message.reply_text("Операций пока нет.", reply_markup=reply_markup)
        else:
            report_text = "Отчёт по операциям:\n"
            for t in data["transactions"]:
                sign = "+" if t["type"] == "income" else "-"
                report_text += f"{sign}{t['amount']:.2f}₴ — {t['desc']}\n"
            await update.message.reply_text(report_text, reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выбери действие кнопками.")
        return ConversationHandler.END

async def amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.replace(',', '.'))
        if amount <= 0:
            raise ValueError
        context.user_data["amount"] = amount
        await update.message.reply_text("Введите описание:")
        return DESCRIPTION
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи корректное число для суммы.")
        return AMOUNT

async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    amount = context.user_data.get("amount")
    op = data.get("operation")

    data["transactions"].append({"type": op, "amount": amount, "desc": desc})

    if op == "income":
        data["balance"] += amount
        await update.message.reply_text(f"Добавлен доход: +{amount:.2f}₴ ({desc})", reply_markup=reply_markup)
    else:
        data["balance"] -= amount
        await update.message.reply_text(f"Добавлен расход: -{amount:.2f}₴ ({desc})", reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=reply_markup)
    return ConversationHandler.END

if __name__ == '__main__':
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Бот запущен...")
    app.run_polling()
