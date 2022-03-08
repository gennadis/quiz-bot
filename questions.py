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
