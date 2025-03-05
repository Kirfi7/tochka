import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from typing import Dict, TypedDict
from faker import Faker


class Item(TypedDict):
    name: str
    price: float


# Имитация базы данных
fake = Faker()
storage: Dict[int, Item] = {
    i: {"name": fake.word(), "price": fake.random_number(digits=5)} for i in range(10)
}


class SimpleHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200) -> None:
        """
        Устанавливает заголовки HTTP-ответа.
        :param status: Код состояния HTTP
        """
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def _send_error(self, status: int, message: str) -> None:
        """
        Отправляет JSON-ошибку с заданным статусом и сообщением.
        :param status: Код состояния HTTP
        :param message: Сообщение об ошибке
        """
        self._set_headers(status)
        self.wfile.write(json.dumps({"error": message}).encode())

    def do_GET(self) -> None:
        """
        Обрабатывает GET-запрос для получения информации о товаре по ID.
        """
        parsed_path = urlparse(self.path)
        if parsed_path.path.startswith("/items/"):
            try:
                item_id = int(parsed_path.path.split("/")[-1])
                if item_id in storage:
                    self._set_headers()
                    self.wfile.write(json.dumps(storage[item_id]).encode())
                else:
                    self._send_error(404, "Товар не найден")
            except ValueError:
                self._send_error(400, "Некорректный ID")
        else:
            self._send_error(404, "Неверный эндпоинт")

    def do_POST(self) -> None:
        """
        Обрабатывает POST-запрос для создания нового товара.
        """
        content_length: int
        try:
            content_length = int(self.headers["Content-Length"])
        except ValueError:
            self._send_error(400, "Некорректный ID")
        post_data: Item = json.loads(self.rfile.read(content_length))
        item_id = max(storage.keys()) + 1 if storage else 1
        storage[item_id] = post_data
        self._set_headers(201)
        self.wfile.write(json.dumps({"id": item_id}).encode())

    def do_PUT(self) -> None:
        """
        Обрабатывает PUT-запрос для обновления информации о товаре.
        """
        parsed_path = urlparse(self.path)
        try:
            item_id = int(parsed_path.path.split("/")[-1])
            if item_id in storage:
                content_length = int(self.headers["Content-Length"])
                put_data: Item = json.loads(self.rfile.read(content_length))
                storage[item_id] = put_data
                self._set_headers()
                self.wfile.write(json.dumps(storage[item_id]).encode())
            else:
                self._send_error(404, "Товар не найден")
        except ValueError:
            self._send_error(400, "Некорректный ID")

    def do_DELETE(self) -> None:
        """
        Обрабатывает DELETE-запрос для удаления товара по ID.
        """
        parsed_path = urlparse(self.path)
        try:
            item_id = int(parsed_path.path.split("/")[-1])
            if item_id in storage:
                del storage[item_id]
                self._set_headers()
                self.wfile.write(json.dumps({"message": "Товар успешно удален"}).encode())
            else:
                self._send_error(404, "Товар не найден")
        except ValueError:
            self._send_error(400, "Некорректный ID")


# Запуск сервера
if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), SimpleHandler)
    print("Starting server at http://localhost:8080")
    server.serve_forever()