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
    get_random_quiz,
    get_quiz_answer,
    get_redis_connection,
    create_new_user_in_redis,
    update_user_in_redis,
    get_user_stats,
)


logger = logging.getLogger(__file__)


class State(Enum):
    NEW_QUESTION = auto()
    SOLUTION_ATTEMPT = auto()
    SURRENDER = auto()


def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    create_new_user_in_redis(redis=redis_connection, user_id=user_id, system="tg")

    custom_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счет"]]
    markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_text(
        f"Привет, {user_name}! Я - бот для викторин!", reply_markup=markup
    )

    return State.NEW_QUESTION


def handle_new_question_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")
    quiz_number, deserialized_quiz = get_random_quiz(redis_connection)

    update_user_in_redis(
        redis=redis_connection,
        user_id=user_id,
        system="tg",
        latest_question=quiz_number,
    )

    update.message.reply_text(deserialized_quiz["question"])

    return State.SOLUTION_ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_text = update.message.text
    redis_connection: redis.Redis = context.bot_data.get("redis")

    answer = get_quiz_answer(redis=redis_connection, user_id=user_id, system="tg")

    if user_text.lower() == answer.lower():
        update_user_in_redis(
            redis=redis_connection,
            user_id=user_id,
            system="tg",
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
            system="tg",
            total_delta=1,
        )
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return State.SURRENDER


def handle_surrender(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    answer = get_quiz_answer(redis=redis_connection, user_id=user_id, system="tg")

    update.message.reply_text(answer)

    return State.NEW_QUESTION


def handle_score_request(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    redis_connection: redis.Redis = context.bot_data.get("redis")

    correct_answers, total_answers = get_user_stats(
        redis=redis_connection, user_id=user_id, system="tg"
    )

    update.message.reply_text(
        f"Правильных ответов: {correct_answers}. Всего ответов: {total_answers}."
    )

    return


def help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text("Help!")


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def main(tg_token: str, redis_connection: redis.Redis):
    logging.basicConfig(level=logging.INFO)

    updater = Updater(token=tg_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.add_error_handler(error_handler)

    converstaion_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.NEW_QUESTION: [
                MessageHandler(
                    Filters.regex(r"Новый вопрос"),
                    handle_new_question_request,
                    MessageHandler(Filters.regex(r"Мой счет"), handle_score_request),
                ),
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
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")

    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")
    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    main(tg_token, redis_connection)
