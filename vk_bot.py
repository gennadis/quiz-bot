import os

import vk_api
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from questions import get_random_quiz, get_quiz_answer, QUIZ_FILEPATH, REDIS_CONN


def set_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.POSITIVE)

    return keyboard.get_keyboard()


def handle_new_question_request(event: VkLongPoll, vk: vk_api):
    question, answer = get_random_quiz(QUIZ_FILEPATH)
    REDIS_CONN.set(name=event.user_id, value=question)

    vk.messages.send(
        user_id=event.user_id,
        message=question,
        keyboard=set_keyboard(),
        random_id=get_random_id(),
    )


def handle_solution_attempt(event: VkLongPoll, vk: vk_api):
    question = REDIS_CONN.get(name=event.user_id)
    answer = get_quiz_answer(QUIZ_FILEPATH, question.decode("UTF-8"))

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


def main(vk_token: str):
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Новый вопрос":
                handle_new_question_request(event, vk)
            else:
                handle_solution_attempt(event, vk)


if __name__ == "__main__":
    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")

    main(vk_token)
