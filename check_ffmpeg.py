import subprocess
import shutil
import os

print("=== ПРОВЕРКА FFMPEG ===\n")

# Проверка 1: через shutil
ffmpeg_path = shutil.which('ffmpeg')
print(f"1. shutil.which('ffmpeg') = {ffmpeg_path}")

# Проверка 2: через subprocess
try:
    result = subprocess.run(['ffmpeg', '-version'], 
                          capture_output=True, 
                          text=True, 
                          check=True)
    print("2. subprocess.run УСПЕШНО")
    print(f"   Версия: {result.stdout[:100]}...")
except Exception as e:
    print(f"2. Ошибка: {e}")

# Проверка 3: пробуем найти ffmpeg вручную
print("\n3. Поиск ffmpeg в системе:")
possible_paths = [
    r"C:\ffmpeg\bin\ffmpeg.exe",
    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
]
for path in possible_paths:
    if os.path.exists(path):
        print(f"   ✅ Найден: {path}")
    else:
        print(f"   ❌ Не найден: {path}")

# Проверка 4: посмотрим PATH
print("\n4. Текущий PATH (пути где может быть ffmpeg):")
paths = os.environ['PATH'].split(';')
ffmpeg_in_path = False
for path in paths:
    if 'ffmpeg' in path.lower():
        print(f"   ✅ FFMPEG В PATH: {path}")
        ffmpeg_in_path = True

if not ffmpeg_in_path:
    print("   ❌ FFMPEG НЕ найден в PATH!")

# Проверка 5: что в папке C:\ffmpeg\bin
print("\n5. Содержимое C:\\ffmpeg\\bin:")
if os.path.exists(r"C:\ffmpeg\bin"):
    files = os.listdir(r"C:\ffmpeg\bin")
    for file in files:
        if file.endswith('.exe'):
            print(f"   📄 {file}")
else:
    print("   ❌ Папка C:\\ffmpeg\\bin не существует!")