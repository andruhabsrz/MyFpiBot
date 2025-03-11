import requests
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

TOKEN = "8193119140:AAG_pZKGGgIsi4PYIbXW3uMxRt7dhaipFOA"
users = {}  # Храним пользователей и их интервалы рассылки

async def get_fpibank_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=fpi-bank&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        if "fpi-bank" in data and "usd" in data["fpi-bank"]:
            return data["fpi-bank"]["usd"]
        else:
            return None
    except Exception as e:
        return None

async def send_price(context: CallbackContext):
    job = context.job
    user_id = job.chat_id
    price = await get_fpibank_price()

    if price is not None:
        message = f"Текущая цена FPIBANK: {price:.8f} USD"
    else:
        message = "Ошибка получения цены FPIBANK."

    try:
        await context.bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Ошибка отправки пользователю {user_id}: {e}")

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("5 минут", callback_data="5")],
        [InlineKeyboardButton("10 минут", callback_data="10")],
        [InlineKeyboardButton("15 минут", callback_data="15")],
        [InlineKeyboardButton("30 минут", callback_data="30")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери интервал получения цены FPIBANK:", reply_markup=reply_markup)

async def set_interval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id
    interval = int(query.data) * 60  # Переводим минуты в секунды

    # Удаляем старый job, если он есть
    if user_id in users:
        old_job = users[user_id]
        old_job.schedule_removal()

    # Добавляем новый job
    new_job = context.job_queue.run_repeating(send_price, interval=interval, first=5, chat_id=user_id)
    users[user_id] = new_job

    await query.edit_message_text(f"✅ Ты подписался на получение цены FPIBANK каждые {query.data} минут!")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(set_interval))

print("Бот запущен!")
app.run_polling()
