def collect_quiz_pairs():
    with open("quiz-questions/1vs1200.txt", "r", encoding="KOI8-R") as file:
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


if __name__ == "__main__":
    quiz_pairs = collect_quiz_pairs()
    print(quiz_pairs)
