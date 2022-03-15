import json
import os
import random

import redis
from dotenv import load_dotenv

REDIS_QUIZ_ITEMS_HASH_NAME = "quiz_items"


def get_redis_connection(
    db_address: str, db_name: str, db_password: str
) -> redis.Redis:
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


def get_random_quiz(redis: redis.Redis) -> tuple[str, str]:
    random_hash_field = redis.hrandfield(key=REDIS_QUIZ_ITEMS_HASH_NAME)
    random_quiz = redis.hget(name=REDIS_QUIZ_ITEMS_HASH_NAME, key=random_hash_field)

    serialized_quiz = json.loads(random_quiz)
    question, answer = serialized_quiz["question"], serialized_quiz["answer"]

    return question, answer


def get_quiz_answer(filepath: str, question: str) -> str:
    with open(filepath, "r") as file:
        quiz_items = json.load(file)
    full_answer = quiz_items[question]
    short_answer = full_answer.split(".")[0].split("(")[0]

    return short_answer


def format_quiz_for_redis(quiz: tuple[str, str], quiz_number: int) -> tuple[str, str]:
    question, answer = quiz
    formatted_quiz = {
        "question": question,
        "answer": answer,
    }

    redis_key = f"question_{quiz_number}"
    redis_value = json.dumps(formatted_quiz, ensure_ascii=False)

    return redis_key, redis_value


def main():
    load_dotenv()
    quiz_folder = os.getenv("QUIZ_FOLDER")
    quiz_file = os.getenv("QUIZ_FILE")
    quiz_filepath = os.path.join(quiz_folder, quiz_file)

    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")

    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    quiz_items = collect_quiz_items(quiz_folder)
    for number, quiz in enumerate(quiz_items.items(), start=1):
        redis_key, redis_value = format_quiz_for_redis(quiz=quiz, quiz_number=number)
        redis_connection.hset(
            REDIS_QUIZ_ITEMS_HASH_NAME, key=redis_key, value=redis_value
        )


if __name__ == "__main__":
    main()
