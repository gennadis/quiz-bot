# Telegram, Vk QUIZ Bot

This project is a simple QUIZ bot for your Vk group or Telegram.

## Examples
Try this telegram bot: `@dvmn_quizz_bot`

## Features
- `long polling` VK and Telegram API utilization
- Send random question to user and check his solution
- Add your custom QUIZ questions from local `.txt` file
- Heroku ready!
- Redis for storing user's `id`, current `question` and guesses stats
- Get your quiz stats by pressing `Stats` button

## Installation
1. Clone project
```bash
git clone https://github.com/gennadis/quiz-bot.git
cd quiz-bot
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Upload quiz qusestions-answers pairs to `Redis`:
```bash
python questions.py
```

5. Rename `.env.example` to `.env` and fill your secrets in it.  
```bash
TG_TOKEN=your_telegram_bot_token
VK_TOKEN=your_vk_bot_token

DB_ADDRESS=redis_cloud_db_uri:PORT
DB_NAME=your_redis_db_name (`0` by default)
DB_PASSWORD=your_redis_db_password
```

6. Run bots
```bash
python telegram_bot.py
python vk_bot.py
```
