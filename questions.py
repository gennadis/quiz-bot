import json
import os
import sys
from platformdirs import user_runtime_dir

import redis
from dotenv import load_dotenv

QUIZ_FOLDER = "quiz_questions"
REDIS_ITEMS_HASH_NAME = "quiz_items"
REDIS_USERS_HASH_NAME = "quiz_users"


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
    random_hash_field = redis.hrandfield(key=REDIS_ITEMS_HASH_NAME)
    random_quiz = redis.hget(name=REDIS_ITEMS_HASH_NAME, key=random_hash_field)

    quiz_number = random_hash_field.decode("utf-8")
    deserialized_quiz = json.loads(random_quiz)

    return quiz_number, deserialized_quiz


def get_quiz_answer(redis: redis.Redis, user_id: int, system: str) -> str:
    user_redis_id, user_stats = read_user_from_redis(redis, user_id, system)
    quiz_number = user_stats["last_asked_question"]
    quiz = redis.hget(name=REDIS_ITEMS_HASH_NAME, key=quiz_number)

    full_answer = json.loads(quiz)["answer"]
    short_answer = full_answer.split(".")[0].split("(")[0]

    return short_answer


def format_quiz_for_redis(
    quiz: tuple[str, str], question_number: int
) -> tuple[str, str]:
    question, answer = quiz
    formatted_quiz = {
        "question": question,
        "answer": answer,
    }

    quiz_number = f"question_{question_number}"
    serialized_quiz = json.dumps(formatted_quiz, ensure_ascii=False)

    return quiz_number, serialized_quiz


def create_new_user_in_redis(redis: redis.Redis, user_id: int, system: str) -> None:
    redis.hset(
        name=REDIS_USERS_HASH_NAME,
        key=f"user_{system}_{user_id}",
        value=json.dumps(
            {
                "last_asked_question": None,
                "correct_answers": 0,
                "total_answers": 0,
            }
        ),
    )


def read_user_from_redis(
    redis: redis.Redis, user_id: int, system: str
) -> tuple[str, dict]:
    user_redis_id = f"user_{system}_{user_id}"
    user_stats_serialized = redis.hget(
        name=REDIS_USERS_HASH_NAME,
        key=user_redis_id,
    )
    user_stats = json.loads(user_stats_serialized)

    return user_redis_id, user_stats


def update_user_in_redis(
    redis: redis.Redis,
    user_id: int,
    system: str,
    latest_question: str = None,
    correct_delta: int = 0,
    total_delta: int = 0,
) -> None:
    user_redis_id, user_stats = read_user_from_redis(redis, user_id, system)

    if latest_question:
        user_stats["last_asked_question"] = latest_question
    user_stats["correct_answers"] += correct_delta
    user_stats["total_answers"] += total_delta

    redis.hset(
        name=REDIS_USERS_HASH_NAME,
        key=user_redis_id,
        value=json.dumps(user_stats),
    )


def main():
    load_dotenv()
    db_address = os.getenv("DB_ADDRESS")
    db_name = os.getenv("DB_NAME")
    db_password = os.getenv("DB_PASSWORD")
    redis_connection = get_redis_connection(
        db_address=db_address, db_name=db_name, db_password=db_password
    )

    quiz_items = collect_quiz_items(QUIZ_FOLDER)
    for number, quiz in enumerate(quiz_items.items(), start=1):
        quiz_number, serialized_quiz = format_quiz_for_redis(
            quiz=quiz, question_number=number
        )
        redis_connection.hset(
            REDIS_ITEMS_HASH_NAME, key=quiz_number, value=serialized_quiz
        )


if __name__ == "__main__":
    main()
