# stt.py
import os
import logging
import tempfile
from pathlib import Path
import torch
from transformers import pipeline
import torchaudio
import soundfile as sf

# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальная переменная для пайплайна (чтобы загрузить модель 1 раз)
_asr_pipeline = None

# Конфигурация модели
WHISPER_MODEL = "openai/whisper-medium"  # Можно заменить на "openai/whisper-base" для скорости или "openai/whisper-large-v3" для качества
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"STT будет использовать устройство: {DEVICE}")

def init_stt():
    """
    Инициализирует модель распознавания речи (загружается 1 раз)
    """
    global _asr_pipeline
    
    if _asr_pipeline is not None:
        logger.info("STT модель уже загружена")
        return True
    
    try:
        logger.info(f"Загружаем модель STT: {WHISPER_MODEL} на {DEVICE}...")
        
        # Создаем пайплайн для автоматического распознавания речи
        _asr_pipeline = pipeline(
            task="automatic-speech-recognition",
            model=WHISPER_MODEL,
            device=DEVICE
        )
        
        logger.info("✅ STT модель успешно загружена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки STT модели: {e}")
        return False

def transcribe_audio(file_path: str) -> str:
    """
    Транскрибирует аудиофайл в текст
    
    Args:
        file_path: путь к аудиофайлу (ogg, mp3, wav и т.д.)
        
    Returns:
        str: распознанный текст или пустая строка при ошибке
    """
    global _asr_pipeline
    
    # Проверяем, загружена ли модель
    if _asr_pipeline is None:
        if not init_stt():
            return ""
    
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return ""
        
        logger.info(f"Транскрибируем аудио: {file_path}")
        
        # Whisper сам обработает аудио (конвертирует, ресемплит)
        result = _asr_pipeline(
            file_path,
            generate_kwargs={
                "max_new_tokens": 256,  # Максимальная длина текста
                "task": "transcribe",   # transcribe или translate
            },
            return_timestamps=False     # Нам нужен только текст
        )
        
        # Извлекаем текст из результата
        transcribed_text = result.get("text", "").strip()
        
        logger.info(f"✅ Транскрибация завершена. Длина текста: {len(transcribed_text)} символов")
        logger.debug(f"Распознанный текст: {transcribed_text[:100]}...")
        
        return transcribed_text
        
    except Exception as e:
        logger.error(f"❌ Ошибка при транскрибации: {e}")
        return ""

def transcribe_audio_bytes(audio_bytes: bytes, file_ext: str = ".ogg") -> str:
    """
    Транскрибирует аудио из байтов (например, из Telegram)
    
    Args:
        audio_bytes: байты аудиофайла
        file_ext: расширение файла (по умолчанию .ogg для Telegram)
        
    Returns:
        str: распознанный текст
    """
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name
    
    try:
        # Транскрибируем
        text = transcribe_audio(tmp_path)
        return text
    finally:
        # Удаляем временный файл
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {tmp_path}: {e}")

# Альтернативный вариант: если нужна поддержка разных форматов
def convert_audio_to_wav(input_path: str, output_path: str = None) -> str:
    """
    Конвертирует аудио в WAV формат (16kHz, моно) для лучшей совместимости
    
    Whisper умеет сам конвертировать, но если нужен контроль над процессом
    """
    if output_path is None:
        output_path = input_path + "_converted.wav"
    
    try:
        # Загружаем аудио
        waveform, sample_rate = torchaudio.load(input_path)
        
        # Ресемплим до 16kHz если нужно
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        
        # Конвертируем в моно если стерео
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Сохраняем как WAV
        torchaudio.save(output_path, waveform, 16000)
        return output_path
        
    except Exception as e:
        logger.error(f"Ошибка конвертации аудио: {e}")
        return input_path  # Возвращаем оригинал, если не удалось конвертировать