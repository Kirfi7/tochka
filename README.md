# Курс по python от Точки

## Работа с миграциями.
### Создание файла миграций
- Чтобы создать миграцию:
```sh
alembic revision --autogenerate -m "migration name"
```
### Применение миграции
- Применение всех не применённых миграций:
```sh
alembic upgrade head
```
#### Откат миграции
```sh
alembic downgrade -1    # Откатить последнюю
alembic downgrade base  # Откатить все
```
