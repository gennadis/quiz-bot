import logging
import os

import redis
import vk_api
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from questions import get_random_quiz, get_quiz_answer, get_redis_connection


logger = logging.getLogger(__file__)


def set_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.POSITIVE)

    return keyboard.get_keyboard()


def handle_new_question_request(
    event: VkLongPoll,
    vk: vk_api,
    redis_connection: redis.Connection,
    quiz_filepath: str,
):
    question, answer = get_random_quiz(quiz_filepath)
    redis_connection.set(name=event.user_id, value=question)

    vk.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def handle_solution_attempt(
    event: VkLongPoll,
    vk: vk_api,
    redis_connection: redis.Connection,
    quiz_filepath: str,
):
    question = redis_connection.get(name=event.user_id)
    answer = get_quiz_answer(quiz_filepath, question.decode("UTF-8"))

    if event.text.lower() == answer.lower():
        vk.messages.send(
            user_id=event.user_id,
            message="Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
            keyboard=set_keyboard(),
            random_id=get_random_id(),
        )

    else:
        vk.messages.send(
            user_id=event.user_id,
            message="Неправильно… Попробуешь ещё раз?",
            keyboard=set_keyboard(),
            random_id=get_random_id(),
        )


def handle_surrender(
    event: VkLongPoll,
    vk: vk_api,
    redis_connection: redis.Connection,
    quiz_filepath: str,
):
    question = redis_connection.get(name=event.user_id)
    answer = get_quiz_answer(quiz_filepath, question.decode("UTF-8"))

    vk.messages.send(
        user_id=event.user_id,
        message=answer,
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def main(vk_token: str, redis_connection: redis.Connection, quiz_filepath: str):
    logging.basicConfig(level=logging.INFO)

    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.info("VK bot started")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Новый вопрос":
                handle_new_question_request(event, vk, redis_connection, quiz_filepath)
            elif event.text == "Сдаться":
                handle_surrender(event, vk, redis_connection, quiz_filepath)
            else:
                handle_solution_attempt(event, vk, redis_connection, quiz_filepath)


if __name__ == "__main__":
    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")

    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")

    quiz_folder = os.getenv("QUIZ_FOLDER")
    quiz_file = os.getenv("QUIZ_FILE")
    quiz_filepath = os.path.join(quiz_folder, quiz_file)

    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    main(
        vk_token=vk_token,
        redis_connection=redis_connection,
        quiz_filepath=quiz_filepath,
    )
