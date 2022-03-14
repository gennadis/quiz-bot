import json
import os
import random

import redis
from dotenv import load_dotenv

load_dotenv()
DB_URL, DB_PORT = os.getenv("DB_ADDRESS").rsplit(":")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
REDIS_CONN = redis.Redis(host=DB_URL, port=DB_PORT, db=DB_NAME, password=DB_PASSWORD)

QUIZ_FOLDER = "quiz-questions"
QUIZ_FILE = "quiz_items.json"
QUIZ_FILEPATH = os.path.join(QUIZ_FOLDER, QUIZ_FILE)


def parse_quiz_file(filename: str) -> dict:
    with open(filename, "r", encoding="KOI8-R") as file:
        text = file.read()

    parsed_quiz_items = dict()
    questions, answers = [], []

    for line in text.split("\n\n"):
        if line.strip().startswith("Вопрос"):
            _, question_text = line.split(sep=":", maxsplit=1)
            questions.append(question_text.replace("\n", " ").strip())
        elif line.strip().startswith("Ответ"):
            _, full_answer = line.split(sep=":", maxsplit=1)
            short_answer = full_answer.split(".")[0].split("(")[0]
            answers.append(short_answer.replace("\n", " ").strip())

    for question, answer in zip(questions, answers):
        parsed_quiz_items[question] = answer

    return parsed_quiz_items


def collect_quiz_items(folderpath: str) -> dict:
    quiz_items = dict()
    quiz_files = [
        os.path.join(folderpath, filename)
        for filename in os.listdir(folderpath)
        if filename.endswith(".txt")
    ]

    for file in quiz_files:
        parsed_quiz_items = parse_quiz_file(file)
        quiz_items.update(parsed_quiz_items)

    return quiz_items


def get_random_quiz(filepath: str) -> tuple[str, str]:
    with open(filepath, "r") as file:
        quiz_items = json.load(file)
    question, answer = random.choice(list(quiz_items.items()))

    return question, answer


def get_quiz_answer(filepath: str, question: str) -> str:
    with open(filepath, "r") as file:
        quiz_items = json.load(file)
    full_answer = quiz_items[question]
    answer, explanation = full_answer.split(".", maxsplit=1)

    return answer


def main():
    quiz_items = collect_quiz_items(QUIZ_FOLDER)

    with open(QUIZ_FILEPATH, "w") as file:
        json.dump(obj=quiz_items, fp=file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
