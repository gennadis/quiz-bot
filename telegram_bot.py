import logging
import os
import random
from enum import Enum, auto


import telegram
from dotenv import load_dotenv
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    RegexHandler,
)

from questions import get_random_quiz, get_quiz_answer, REDIS_CONN, QUIZ_FILEPATH

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счет"]]
markup = telegram.ReplyKeyboardMarkup(custom_keyboard)


class State(Enum):
    NEW_QUESTION = auto()
    SOLUTION_ATTEMPT = auto()
    SURRENDER = auto()


def start(bot, update):
    update.message.reply_text("Привет! Я - бот для викторин!", reply_markup=markup)

    return State.NEW_QUESTION


def handle_new_question_request(bot, update):
    question, answer = get_random_quiz(QUIZ_FILEPATH)
    REDIS_CONN.set(name=update.message.chat_id, value=question)
    update.message.reply_text(question)

    return State.SOLUTION_ATTEMPT


def handle_solution_attempt(bot, update):
    question = REDIS_CONN.get(name=update.message.chat_id)
    answer = get_quiz_answer(QUIZ_FILEPATH, question.decode("UTF-8"))

    if update.message.text.lower() == answer.lower():
        update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
        )
        return State.NEW_QUESTION
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return State.SURRENDER


def handle_surrender(bot, update):
    question = REDIS_CONN.get(name=update.message.chat_id)
    answer = get_quiz_answer(QUIZ_FILEPATH, question.decode("UTF-8"))

    update.message.reply_text(answer)

    return State.NEW_QUESTION


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

    converstaion_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.NEW_QUESTION: [
                RegexHandler("Новый вопрос", handle_new_question_request)
            ],
            State.SURRENDER: [RegexHandler("Сдаться", handle_surrender)],
            State.SOLUTION_ATTEMPT: [
                MessageHandler(Filters.text, handle_solution_attempt)
            ],
        },
        fallbacks=[],
    )

    dp = updater.dispatcher
    dp.add_handler(converstaion_handler)

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
