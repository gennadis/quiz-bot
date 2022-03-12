import os
import random

import vk_api
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id


def main(vk_token: str):
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счет", color=VkKeyboardColor.POSITIVE)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            vk.messages.send(
                peer_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message="Пример клавиатуры",
            )


if __name__ == "__main__":
    load_dotenv()
    vk_token = os.getenv("VK_TOKEN")

    main(vk_token)
