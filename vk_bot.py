import logging
import os

import redis
import vk_api
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from questions import (
    get_random_quiz,
    get_quiz_answer,
    get_redis_connection,
    update_user_in_redis,
    get_user_stats,
)


VK_MESSENGER = "vk"

logger = logging.getLogger(__file__)


def set_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.POSITIVE)

    return keyboard.get_keyboard()


def handle_new_question_request(
    event: VkLongPoll, vk: vk_api, redis_connection: redis.Redis
) -> None:
    user_id = event.user_id
    quiz_number, deserialized_quiz = get_random_quiz(redis_connection)

    update_user_in_redis(
        redis=redis_connection,
        user_id=user_id,
        messenger=VK_MESSENGER,
        latest_question=quiz_number,
    )

    vk.messages.send(
        user_id=user_id,
        message=deserialized_quiz["question"],
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def handle_solution_attempt(
    event: VkLongPoll, vk: vk_api, redis_connection: redis.Redis
) -> None:
    user_id = event.user_id
    user_text = event.text
    answer = get_quiz_answer(
        redis=redis_connection, user_id=user_id, messenger=VK_MESSENGER
    )

    if user_text.lower() == answer.lower():
        update_user_in_redis(
            redis=redis_connection,
            user_id=user_id,
            messenger=VK_MESSENGER,
            correct_delta=1,
            total_delta=1,
        )

        vk.messages.send(
            user_id=user_id,
            message="Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
            keyboard=set_keyboard(),
            random_id=get_random_id(),
        )

    else:
        update_user_in_redis(
            redis=redis_connection,
            user_id=user_id,
            messenger=VK_MESSENGER,
            total_delta=1,
        )

        vk.messages.send(
            user_id=event.user_id,
            message="Неправильно… Попробуешь ещё раз?",
            keyboard=set_keyboard(),
            random_id=get_random_id(),
        )


def handle_surrender(
    event: VkLongPoll, vk: vk_api, redis_connection: redis.Redis
) -> None:
    user_id = event.user_id
    answer = get_quiz_answer(
        redis=redis_connection, user_id=user_id, messenger=VK_MESSENGER
    )

    vk.messages.send(
        user_id=user_id,
        message=answer,
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def handle_score_request(event: VkLongPoll, vk: vk_api, redis_connection: redis.Redis):
    user_id = event.user_id
    correct_answers, total_answers = get_user_stats(
        redis=redis_connection, user_id=user_id, messenger=VK_MESSENGER
    )

    vk.messages.send(
        user_id=user_id,
        message=f"Правильных ответов: {correct_answers}. Всего ответов: {total_answers}.",
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")

    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")
    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.info("VK bot started")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Новый вопрос":
                handle_new_question_request(event, vk, redis_connection)
            elif event.text == "Сдаться":
                handle_surrender(event, vk, redis_connection)
            else:
                handle_solution_attempt(event, vk, redis_connection)


if __name__ == "__main__":
    main()
