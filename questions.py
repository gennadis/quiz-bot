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
            questions.append(line)
        elif line.strip().startswith("Ответ"):
            answers.append(line)

    for question, answer in zip(questions, answers):
        quiz_pairs[question] = answer

    return quiz_pairs
