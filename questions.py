import os

import redis
from dotenv import load_dotenv

load_dotenv()
DB_URL, DB_PORT = os.getenv("DB_ADDRESS").rsplit(":")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
REDIS_CONN = redis.Redis(host=DB_URL, port=DB_PORT, db=DB_NAME, password=DB_PASSWORD)


def collect_quiz_pairs(filename: str) -> dict:
    with open(filename, "r", encoding="KOI8-R") as file:
        text = file.read()

    quiz_pairs = dict()
    questions, answers = [], []

    for line in text.split("\n\n"):
        if line.strip().startswith("Вопрос"):
            _, question_text = line.split(sep=":", maxsplit=1)
            questions.append(question_text.strip())
        elif line.strip().startswith("Ответ"):
            _, answer_text = line.split(sep=":", maxsplit=1)
            answers.append(answer_text.strip())

    for question, answer in zip(questions, answers):
        quiz_pairs[question] = answer

    return quiz_pairs
