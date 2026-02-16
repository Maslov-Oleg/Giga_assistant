import os
import logging
import tempfile
from pathlib import Path
import torch
from transformers import pipeline
import torchaudio
import soundfile as sf


logger = logging.getLogger(__name__)

# Глобальная переменная для пайплайна (чтобы загрузить модель 1 раз)
_asr_pipeline = None

# Конфигурация модели
WHISPER_MODEL = "openai/whisper-medium"  # "openai/whisper-base", "openai/whisper-large-v3" 
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"STT будет использовать устройство: {DEVICE}")

# Инициализируем модель распознавания речи
def init_stt():
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

# транскребируем аудиофайл в текст
def transcribe_audio(file_path: str) -> str:
    global _asr_pipeline
    

    if _asr_pipeline is None:
        if not init_stt():
            return ""
    
    try:
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return ""
        
        logger.info(f"Транскрибируем аудио: {file_path}")
        
        # Whisper 
        result = _asr_pipeline(
            file_path,
            generate_kwargs={
                "max_new_tokens": 256,  # Максимальная длина текста
                "task": "transcribe",   
            },
            return_timestamps=False     
        )
        
        # Извлекаем текст из результата
        transcribed_text = result.get("text", "").strip()
        
        logger.info(f"✅ Транскрибация завершена. Длина текста: {len(transcribed_text)} символов")
        logger.debug(f"Распознанный текст: {transcribed_text[:100]}...")
        
        return transcribed_text
        
    except Exception as e:
        logger.error(f"❌ Ошибка при транскрибации: {e}")
        return ""

# Транскрибируем аудио из байтов
def transcribe_audio_bytes(audio_bytes: bytes, file_ext: str = ".ogg") -> str:

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

# Альтернативный вариант, если нужна поддержка разных форматов
def convert_audio_to_wav(input_path: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = input_path + "_converted.wav"
    
    try:
        # Загружаем аудио
        waveform, sample_rate = torchaudio.load(input_path)
        
        # Ресемплим до 16kHz 
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