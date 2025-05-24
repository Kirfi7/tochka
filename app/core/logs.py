import logging
import os
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Any

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


# 🚨 Декоратор для логирования ошибок
def error_log(func):
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            app_logger.error(
                f"Can't do this operation in DB in method {func.__name__}. Error: {e}"
            )
            raise e

    return wrapper