import os
from pathlib import Path


try:
    from docx import Document
except ImportError:
    print("python-docx не установлен")
    raise
# загружает документ и возвращает его текст, .txt .docx
def load_document(filepath: str) -> str:

    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Файл {filepath} не найден")
    
    # Определяем тип файла по расширению
    extension = filepath.suffix.lower()
    
    if extension == '.txt':
        return _load_txt(filepath)
    elif extension == '.docx':
        return _load_docx(filepath)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {extension}. Используйте .txt или .docx")

# загружаем текстовый файл
def _load_txt(filepath: Path) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# Загружает Word документ
def _load_docx(filepath: Path) -> str:
    doc = Document(filepath)
    # Собираем весь текст из документа
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                full_text.append(cell.text)
    
    return '\n'.join(full_text)