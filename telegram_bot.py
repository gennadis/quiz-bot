import logging
import os
from enum import Enum, auto

import redis
import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from questions import (
    get_redis_connection,
    get_random_quiz,
    create_new_user_in_redis,
    read_user_from_redis,
    update_user_in_redis,
)

TG_MESSENGER = "tg"

logger = logging.getLogger(__file__)


class State(Enum):
    NEW_QUESTION = auto()
    SOLUTION_ATTEMPT = auto()
    SURRENDER = auto()


def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    create_new_user_in_redis(
        redis=redis_connection, user_id=user_id, messenger=TG_MESSENGER
    )

    custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счет"]]
    markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text(
        f"Привет, {user_name}! Я - бот для викторин!", reply_markup=markup
    )

    return State.NEW_QUESTION


def handle_new_question_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")
    question, answer = get_random_quiz(redis=redis_connection)

    update_user_in_redis(
        redis=redis_connection,
        user_id=user_id,
        messenger=TG_MESSENGER,
        question=question,
        answer=answer,
    )

    update.message.reply_text(question)

    return State.SOLUTION_ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_text = update.message.text
    redis_connection: redis.Redis = context.bot_data.get("redis")

    user_redis_id, user_stats = read_user_from_redis(
        redis=redis_connection, user_id=user_id, messenger=TG_MESSENGER
    )
    answer = user_stats["answer"]

    if user_text.lower() == answer.lower():
        update_user_in_redis(
            redis=redis_connection,
            user_id=user_id,
            messenger=TG_MESSENGER,
            correct_delta=1,
            total_delta=1,
        )
        update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
        )
        return State.NEW_QUESTION
    else:
        update_user_in_redis(
            redis=redis_connection,
            user_id=user_id,
            messenger=TG_MESSENGER,
            total_delta=1,
        )
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return State.SURRENDER


def handle_surrender(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    user_redis_id, user_stats = read_user_from_redis(
        redis=redis_connection, user_id=user_id, messenger=TG_MESSENGER
    )
    answer = user_stats["answer"]

    update.message.reply_text(answer)

    return State.NEW_QUESTION


def handle_score_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    user_redis_id, user_stats = read_user_from_redis(
        redis=redis_connection, user_id=user_id, messenger=TG_MESSENGER
    )
    correct_answers = user_stats["correct_answers"]
    total_answers = user_stats["total_answers"]

    update.message.reply_text(
        f"Правильных ответов: {correct_answers}. Всего ответов: {total_answers}."
    )


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")

    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")
    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    updater = Updater(token=tg_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.add_error_handler(error_handler)

    converstaion_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.NEW_QUESTION: [
                MessageHandler(
                    Filters.regex(r"Новый вопрос"), handle_new_question_request
                ),
                MessageHandler(Filters.regex(r"Мой счет"), handle_score_request),
            ],
            State.SURRENDER: [
                MessageHandler(Filters.regex(r"Сдаться"), handle_surrender),
                MessageHandler(Filters.regex(r"Мой счет"), handle_score_request),
                MessageHandler(Filters.text, handle_solution_attempt),
            ],
            State.SOLUTION_ATTEMPT: [
                MessageHandler(Filters.regex(r"Сдаться"), handle_surrender),
                MessageHandler(Filters.regex(r"Мой счет"), handle_score_request),
                MessageHandler(Filters.text, handle_solution_attempt),
            ],
        },
        fallbacks=[],
    )

    dispatcher.add_handler(converstaion_handler)

    updater.start_polling()
    updater.idle()
    logger.info("Telegram bot started")


if __name__ == "__main__":
    main()
