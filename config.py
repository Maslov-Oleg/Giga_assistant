import os
from dotenv import load_dotenv

load_dotenv()

GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = "@Giga_AssistantBot"


LECTURE_DOCUMENT_PATH = "./речь_спикера.docx"  


if not GIGACHAT_API_KEY:
    raise ValueError("Не найден GIGACHAT_API_KEY в .env файле")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле")