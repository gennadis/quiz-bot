import json
import os
import random

import redis

QUIZ_FOLDER = "quiz-questions"
QUIZ_FILE = "quiz_items.json"
QUIZ_FILEPATH = os.path.join(QUIZ_FOLDER, QUIZ_FILE)


def get_redis_connection(
    db_address: str, db_name: str, db_password: str
) -> redis.Connection:
    db_url, db_port = db_address.rsplit(":")
    redis_connection = redis.Redis(
        host=db_url, port=db_port, db=db_name, password=db_password
    )

    return redis_connection


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
            _, answer_text = line.split(sep=":", maxsplit=1)
            answers.append(answer_text.replace("\n", " ").strip())

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
    short_answer = full_answer.split(".")[0].split("(")[0]

    return short_answer


def main():
    quiz_items = collect_quiz_items(QUIZ_FOLDER)

    with open(QUIZ_FILEPATH, "w") as file:
        json.dump(obj=quiz_items, fp=file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
