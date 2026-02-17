import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold, hitalic

import config
import agent
import stt

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


BOT_NAMES = [
    "Гигачат", "гигачат", "Гига", "гига",
    "Gigachat", "gigachat", "Giga", "giga",
    "ассистент"]

# Добавляем имя бота из конфига
if hasattr(config, 'BOT_NAME') and config.BOT_NAME:
    BOT_NAMES.append(config.BOT_NAME)

# Проверяем права администратора
async def is_admin(message: Message) -> bool:
    if message.chat.type == "private":
        return True  # В личке считаем админом
    
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    return member.status in ["creator", "administrator"]

# Проверяем, есть ли обращение к боту
def is_bot_mentioned(text: str) -> bool:
    if not text or not text.strip():
        return False
    
    first_word = text.strip().split()[0].lower().strip('.,!?;:')
    
    # Проверяем 1 слово
    if first_word in BOT_NAMES:
        logger.info(f"Найдено обращение: '{first_word}'")
        return True
    
    # Проверяем обращение с @
    if first_word.startswith('@') and first_word[1:].lower() in [name.lower().replace('@', '') for name in BOT_NAMES]:
        logger.info(f"Найдено обращение через @: '{first_word}'")
        return True
    
    return False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет! Я AI-ассистент спикера.\n\n"
        "Я изучил текст выступления и готов отвечать на ваши вопросы.\n\n"
        "❓Чтобы задать вопрос обратесь ко мне по имени.\n"
        "Некоторые допустимые обращения: Gigachat, Гигачат, Giga, Гига или @Giga_AssistantBot.\n\n"
        "🎤 Вы также можете использовать аудиосообщения!\n\n"
        "Пример: Гигачат, какие три новых простых правила жизни внутри компании ввел спикер?"
    )

# перезагрузка агента (админы)
@dp.message(Command("reload"))
async def cmd_reload(message: Message):
    if not await is_admin(message):
        await message.reply("❌ Только администраторы группы могут перезагружать агента")
        return
    
    status_msg = await message.reply("🔄 Перезагружаю агента и сбрасываю историю...")
    
    if agent.reload_agent():
        await status_msg.edit_text("✅ Агент успешно перезагружен!")
    else:
        await status_msg.edit_text("❌ Ошибка при перезагрузке агента")

# сброс истории диалога (админы)
@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    if not await is_admin(message):
        await message.reply("❌ Только администраторы могут сбрасывать историю диалога")
        return
    
    # Переинициализируем агента
    agent.reload_agent()
    await message.reply("🔄 История диалога сброшена. Можете задавать новые вопросы!")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = help_text = f"""📚 Как пользоваться ботом:

В группе обращайтесь к боту по имени: {', '.join(BOT_NAMES)}

Пример: Гигачат, какой основной вывод лекции?

• Агент отвечает только на текстовые и голосовые сообщения, которые начинаются с обращения.

• ИИ-агент работает строго по материалу спикера и не пользуется дополнительной информацией.

🔥 Доступные команды:
/start - начать работу
/help - справка
/reset - сбросить историю диалога (только для админов)
/report - создать отчет по речи спикера (только для админов)"""
    
    await message.answer(help_text)

# обработка команды итогово вывода файла
@dp.message(Command("report"))
async def make_report(message: Message):
    if not await is_admin(message):
        await message.reply("❌ Только администраторы могут сбрасывать историю диалога")
        return

    status_msg = await message.reply("📊 Начинаю создание отчёта по конференции..."
                                     "\nЭто может занять некоторое время.")
    # импорт и инициализация бота суммарайзера
    from summarizer import Summarizer
    summa = Summarizer(config.GIGACHAT_SUMMARIZATION_API_KEY)
    output_filename = "Отчёт_по_конференции.pdf"

    await status_msg.edit_text(
        f"{status_msg.text}\n"
        f"🔄 Обрабатываю запрос к GigaChat..."
    )

    # запуск создания отчёта
    summa.create_report(config.QUESTION_DOCUMENT_PATH, output_filename)

    # проверка, создался ли файл
    if os.path.exists(output_filename):
        with open(output_filename, 'rb') as pdf_file:
            await message.reply_document(
                document=pdf_file,
                caption=f"✅ Отчёт успешно создан!\nФайл: {output_filename}",
                reply_to_message_id=message.message_id
            )

        await status_msg.delete()
        # os.remove(output_filename)

    else:
        await status_msg.edit_text("❌ Не удалось создать PDF-файл с отчётом")

# обработка текстовых сообщений с проверкой обращений
@dp.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_text(message: Message):
    
    # Проверяем есть ли обращение к боту?
    if not is_bot_mentioned(message.text):

        logger.info(f"Игнорируем сообщение без обращения от {message.from_user.full_name}: {message.text[:30]}...")
        return
    
    logger.info(f"Обработка вопроса с обращением от {message.from_user.full_name}: {message.text[:50]}...")
    

    user_name = message.from_user.first_name or message.from_user.username or "Слушатель"
    
    words = message.text.strip().split()
    if len(words) > 1:
        # Убираем запятую после обращения, если есть
        question_text = ' '.join(words[1:]).lstrip(', ')
    else:
        question_text = ""  
    
    # Если после обращения ничего нет - просим задать вопрос
    if not question_text:
        await message.reply(
            f"""{user_name}, я слушаю! Задайте ваш вопрос по лекции.\nПамятка - /help""",
            reply_to_message_id=message.message_id
        )
        return
    
    # Показываем, что бот печатает
    await bot.send_chat_action(message.chat.id, action="typing")
    
    # Получаем ответ от агента
    answer = agent.ask_agent(question_text)
    personalized_answer = f"{user_name}, {answer}"
    
    # Отправляем ответ с reply на сообщение пользователя
    await message.reply(
        personalized_answer,
        reply_to_message_id=message.message_id
    )

# Обработчик голосовых сообщений
@dp.message(lambda message: message.voice)
async def handle_voice(message: Message):
    logger.info(f"Голосовое от {message.from_user.full_name}")
    
    user_name = message.from_user.first_name or message.from_user.username or "Слушатель"
    
    # Проверяем текстовую подпись к голосовому (если есть)
    if message.caption and is_bot_mentioned(message.caption):
        logger.info(f"Голосовое с текстовой подписью-обращением")
        
        # Удаляем обращение из подписи
        words = message.caption.strip().split()
        if len(words) > 1:
            question_text = ' '.join(words[1:]).lstrip(', ')
        else:
            question_text = ""
        
        if question_text:
            await bot.send_chat_action(message.chat.id, action="typing")
            
            # Получаем ответ от агента
            answer = agent.ask_agent(question_text)
            personalized_answer = f"{user_name}, {answer}"
            
            # Отправляем ответ 
            await message.reply(
                personalized_answer,
                reply_to_message_id=message.message_id
            )
        else:
            # Если в подписи только обращение без вопроса
            await message.reply(
                f"{user_name}, я слушаю! Задайте ваш вопрос.",
                reply_to_message_id=message.message_id
            )
        return
    
    # Если нет подписи, скачиваем аудио для распознавания
    try:
        # Скачиваем голосовое сообщение
        file = await bot.get_file(message.voice.file_id)
        file_path = f"voice_{message.from_user.id}_{message.message_id}.ogg"
        await bot.download_file(file.file_path, file_path)
        
        # Транскрибируем аудио
        logger.info("Запускаем транскрибацию...")
        transcribed_text = stt.transcribe_audio(file_path)
        
        os.remove(file_path)
        
        if not transcribed_text:
            # Если не удалось распознать - просто игнорируем (без уведомления)
            logger.info("Не удалось распознать голосовое сообщение - игнорируем")
            return
        
        logger.info(f"Распознанный текст: {transcribed_text[:100]}...")
        
        # Проверяем, есть ли обращение в распознанном тексте
        if is_bot_mentioned(transcribed_text):
            logger.info("Обнаружено обращение к боту в голосовом сообщении")
            
            # Отправляем уведомление о начале обработки
            processing_msg = await message.reply(
                f"{user_name}, 🎤 распознаю ваше голосовое сообщение...",
                reply_to_message_id=message.message_id
            )
            
            # Удаляем обращение из текста
            words = transcribed_text.strip().split()
            if len(words) > 1:
                question_text = ' '.join(words[1:]).lstrip(', ')
            else:
                question_text = ""
            
            if question_text:
                # Получаем ответ от агента
                await bot.send_chat_action(message.chat.id, action="typing")
                answer = agent.ask_agent(question_text)
                personalized_answer = f"{user_name}, {answer}"
                
                # Обновляем сообщение о процессе на финальный ответ
                await processing_msg.edit_text(
                    personalized_answer,
                    reply_to_message_id=message.message_id
                )
            else:
                # Если после обращения нет текста
                await processing_msg.edit_text(
                    f"{user_name}, я слушаю! Задайте ваш вопрос.",
                    reply_to_message_id=message.message_id
                )
        else:
            logger.info("В распознанном тексте нет обращения к боту - игнорируем")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке голоса: {e}")
        pass

# Тестирование STT
@dp.message(Command("test_stt"))
async def cmd_test_stt(message: Message):
    if not await is_admin(message):
        await message.reply("❌ Только администраторы могут тестировать STT")
        return
    
    await message.reply(
        "🔄 Инициализирую STT модель...\n"
        f"Модель: {stt.WHISPER_MODEL}\n"
        f"Устройство: {stt.DEVICE}"
    )
    
    if stt.init_stt():
        await message.reply("✅ STT модель успешно загружена и готова к работе!")
    else:
        await message.reply("❌ Ошибка загрузки STT модели")

# остальные типы сообщений просто игнорируем
@dp.message(lambda message: message.new_chat_members)
async def ignore_new_members(message: Message):

    logger.info(f"Новый участник в чате: {message.new_chat_members}")

@dp.message(lambda message: message.left_chat_member)
async def ignore_left_members(message: Message):
    logger.info(f"Участник покинул чат: {message.left_chat_member}")

@dp.message(lambda message: message.photo)
async def ignore_photo(message: Message):
    logger.info(f"Фото от {message.from_user.full_name}, игнорируем")

@dp.message(lambda message: message.sticker)
async def ignore_sticker(message: Message):
    logger.info(f"Стикер от {message.from_user.full_name}, игнорируем")

@dp.message(lambda message: message.document)
async def ignore_document(message: Message):
    logger.info(f"Документ от {message.from_user.full_name}, игнорируем")

# Основная функция 
async def main():
    logger.info(f"Загружены обращения: {BOT_NAMES}")
    
    # Инициализируем агента (загружаем документ)
    logger.info("Инициализация агента...")
    if not agent.init_agent():
        logger.error("Не удалось загрузить документ! Бот будет работать без знаний.")
    
    # Инициализируем STM модель
    logger.info("Инициализация STT...")
    stt.init_stt()
    
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())