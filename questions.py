import json
import os

import redis
from dotenv import load_dotenv
from tqdm import tqdm

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
    random_question = redis.hrandfield(key=REDIS_ITEMS_HASH_NAME)
    random_answer = redis.hget(name=REDIS_ITEMS_HASH_NAME, key=random_question)

    question, answer = list(
        map(lambda x: x.decode("utf-8"), (random_question, random_answer))
    )

    return question, answer


def create_new_user_in_redis(redis: redis.Redis, user_id: int, messenger: str) -> None:
    redis.hset(
        name=REDIS_USERS_HASH_NAME,
        key=f"user_{messenger}_{user_id}",
        value=json.dumps(
            {
                "question": None,
                "answer": None,
                "correct_answers": 0,
                "total_answers": 0,
            }
        ),
    )


def read_user_from_redis(
    redis: redis.Redis, user_id: int, messenger: str
) -> tuple[str, dict]:
    user_redis_id = f"user_{messenger}_{user_id}"
    user_stats_serialized = redis.hget(
        name=REDIS_USERS_HASH_NAME,
        key=user_redis_id,
    )
    user_stats = json.loads(user_stats_serialized)

    return user_redis_id, user_stats


def update_user_in_redis(
    redis: redis.Redis,
    user_id: int,
    messenger: str,
    question: str = None,
    answer: str = None,
    correct_delta: int = 0,
    total_delta: int = 0,
) -> None:
    user_redis_id, user_stats = read_user_from_redis(redis, user_id, messenger)

    if question and answer:
        # store short answer only
        user_stats["question"] = question
        user_stats["answer"] = answer.split(".")[0].split("(")[0]

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

    for question, answer in tqdm(
        iterable=collect_quiz_items(QUIZ_FOLDER).items(),
        desc="Uploading quiz items",
        unit="items",
    ):
        redis_connection.hset(REDIS_ITEMS_HASH_NAME, key=question, value=answer)


if __name__ == "__main__":
    main()
