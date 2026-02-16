# agent.py
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import config
import document_loader

# Глобальные переменные для хранения состояния агента
_lecture_text = ""
_gigachat_client = None
_chat_history = []  # Будем хранить историю сообщений

def init_agent():
    """
    Инициализирует агента: загружает документ и создаёт сессию GigaChat
    """
    global _lecture_text, _gigachat_client, _chat_history
    
    print(f"Загружаем документ: {config.LECTURE_DOCUMENT_PATH}")
    try:
        _lecture_text = document_loader.load_document(config.LECTURE_DOCUMENT_PATH)
        print(f"Документ загружен. Длина текста: {len(_lecture_text)} символов")
        
        # Создаём клиента GigaChat
        _gigachat_client = GigaChat(credentials=config.GIGACHAT_API_KEY, verify_ssl_certs=False)
        
        # Отправляем лекцию как системное сообщение (только 1 раз!)
        _chat_history = [
            Messages(
                role=MessagesRole.SYSTEM, 
                content=f"""Ты - ассистент спикера на лекции. Твоя задача - отвечать на вопросы слушателей, используя ТОЛЬКО информацию из текста лекции ниже.

ТЕКСТ ЛЕКЦИИ:
----------------------------------------
{_lecture_text}
----------------------------------------

ВАЖНЫЕ ПРАВИЛА:
1. Отвечай только на основе текста лекции
2. Если информация отсутствует в лекции, честно скажи: "В лекции не рассматривается этот вопрос"
3. Не добавляй свои знания и не придумывай факты
4. Отвечай на том языке, на котором задан вопрос"""
            )
        ]
        
        print("Агент инициализирован, лекция загружена в системный промпт")
        return True
        
    except Exception as e:
        print(f"ОШИБКА инициализации агента: {e}")
        return False

def ask_agent(question: str) -> str:
    """
    Задает вопрос агенту и получает ответ строго по документу
    """
    global _gigachat_client, _chat_history
    
    # Проверяем, инициализирован ли агент
    if not _gigachat_client or not _chat_history:
        return "❌ Ошибка: агент не инициализирован. Обратитесь к администратору."
    
    if not question or not question.strip():
        return "Пожалуйста, задайте вопрос."
    
    try:
        # Добавляем вопрос пользователя в историю
        user_message = Messages(role=MessagesRole.USER, content=question)
        _chat_history.append(user_message)
        
        # Отправляем всю историю в GigaChat
        response = _gigachat_client.chat(Chat(messages=_chat_history))
        
        # Получаем ответ ассистента
        assistant_answer = response.choices[0].message.content
        
        # Добавляем ответ ассистента в историю (чтобы модель помнила контекст)
        assistant_message = Messages(role=MessagesRole.ASSISTANT, content=assistant_answer)
        _chat_history.append(assistant_message)
        
        # Для отладки можно посмотреть длину истории
        print(f"История диалога: {len(_chat_history)} сообщений")
        
        return assistant_answer
            
    except Exception as e:
        print(f"Ошибка при запросе к GigaChat: {e}")
        return "❌ Произошла ошибка при обращении к GigaChat. Попробуйте позже."

def reload_agent():
    """Перезагружает агента (сбрасывает историю и заново загружает лекцию)"""
    global _gigachat_client, _chat_history
    
    # Закрываем старого клиента, если есть
    if _gigachat_client:
        try:
            _gigachat_client.close()
        except:
            pass
    
    # Заново инициализируем
    return init_agent()