# Response Envelope

**File:** `src/app/rabbit/models/base.py`

Стандартный конверт для всех ответов RabbitMQ. Все хендлеры возвращают `ResponseMessage[T]`, где `T` — конкретный тип данных ответа.

## ResponseMessage[T]

Generic конверт для всех ответов.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `int` | HTTP-подобный статус-код (200 = успех, 4xx/5xx = ошибка) |
| `message` | `T` | Тело ответа (тип зависит от контракта) |

## ErrorResponse

Используется как `T` в ошибочных ответах.

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | Текст ошибки |

Middleware перехватывает `DomainException` и формирует `ResponseMessage[ErrorResponse]` с соответствующим `status_code` и `message`.

## StatusResponse

Используется для операций, возвращающих только статус.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"ok"` | Статус операции |

## UpdateResponse

Используется для операций обновления.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"ok"` | Статус операции |
| `updated` | `bool` | `True` | Флаг успешности обновления |
