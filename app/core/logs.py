import logging
from logging.handlers import RotatingFileHandler
import os

# TODO: переделать, то директория для логов существует
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Основной логгер приложения
app_logger = logging.getLogger("app_logger")
app_logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

# Файловый обработчик с ротацией
file_handler = RotatingFileHandler(
    filename=os.path.join(LOG_DIR, "app.log"),
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

# Обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Добавляем обработчики
app_logger.addHandler(file_handler)
app_logger.addHandler(console_handler)
