import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from faker import Faker

app = FastAPI()


# Описание модели данных
class Item(BaseModel):
    name: str
    price: float


# Имитация базы данных
fake = Faker()
storage: Dict[int, Item] = {i: Item(name=fake.word(), price=fake.random_number(digits=5)) for i in range(10)}


@app.post("/items/", response_model=int)
def create_item(item: Item) -> int:
    """
    Добавляет новый товар в хранилище.

    :param item: Объект Item с названием и ценой
    :return: ID добавленного товара
    """
    item_id = max(storage.keys()) + 1 if storage else 0
    storage[item_id] = item
    return item_id


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    """
    Получает информацию о товаре по ID.

    :param item_id: Идентификатор товара
    :return: Объект Item с информацией о товаре
    """
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item not found.")
    return storage[item_id]


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: Item) -> Item:
    """
    Обновляет информацию о существующем товаре.

    :param item_id: Идентификатор товара
    :param item: Обновленные данные товара
    :return: Обновленный объект Item
    """
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item не найден")
    storage[item_id] = item
    return item


@app.delete("/items/{item_id}", response_model=str)
def delete_item(item_id: int) -> str:
    """
    Удаляет товар по его ID.

    :param item_id: Идентификатор товара
    :return: Сообщение об успешном удалении
    """
    if item_id not in storage:
        raise HTTPException(status_code=404, detail="Item не найден")
    del storage[item_id]
    return "Item удалён"


# Запуск сервера
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
