import logging
import os
import random

import telegram
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from questions import collect_quiz_pairs, REDIS_CONN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(bot, update):
    custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счет"]]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Привет! Я - бот для викторин!",
        reply_markup=reply_markup,
    )


def send_question(bot, update):
    quiz_pairs = collect_quiz_pairs("quiz-questions/1vs1200.txt")
    question, answer = random.choice(list(quiz_pairs.items()))

    REDIS_CONN.set(name=update.message.chat_id, value=question)
    update.message.reply_text(question)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Help!")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")

    updater = Updater(token=tg_token)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.regex("Новый вопрос"), send_question))
    dp.add_handler(MessageHandler(Filters.text, help))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
