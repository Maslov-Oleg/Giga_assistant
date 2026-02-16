# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Токены и ключи
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = "@Giga_AssistantBot"

# Путь к документу с лекцией (мы его знаем заранее)
# Можешь указать абсолютный или относительный путь
LECTURE_DOCUMENT_PATH = "./речь_спикера.docx"  # или "./lecture.txt"

# Проверка наличия ключей
if not GIGACHAT_API_KEY:
    raise ValueError("Не найден GIGACHAT_API_KEY в .env файле")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле")