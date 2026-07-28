# Domain Exceptions

**File:** `src/core/exceptions.py`

Иерархия доменных исключений. Все наследуются от базового `DomainException` и перехватываются middleware-слоем RabbitMQ хендлеров, который преобразует их в `ResponseMessage[ErrorResponse]` с соответствующим HTTP-подобным статус-кодом.

## Hierarchy

```
DomainException(status_code, message)
├── NotAuthorizedException          # 401
├── BadRequestException             # 400
├── ForbiddenException              # 403
├── NotFoundException               # 404
├── ExceedRetryLimitException       # 409
├── MigrationException              # 409
└── InternalLogicException          # 500
```

## Base Exception

### `DomainException(status_code: int, message: str)`

Базовый класс для всех доменных исключений. Содержит `status_code` (int) и `message` (str), которые передаются в ответ клиенту.

Middleware всех RabbitMQ хендлеров перехватывает `DomainException` и возвращает:

```json
{
  "status": <status_code>,
  "message": { "message": "<error text>" }
}
```

## Exception Types

| Exception | Status Code | Constructor | Condition |
|-----------|-------------|-------------|-----------|
| `NotAuthorizedException` | 401 | `NotAuthorizedException()` | Пользователь не аутентифицирован |
| `BadRequestException` | 400 | `BadRequestException(message: str)` | Некорректный запрос / валидация |
| `ForbiddenException` | 403 | `ForbiddenException(message: str)` | Недостаточно прав |
| `NotFoundException` | 404 | `NotFoundException(message: str)` | Сущность не найдена |
| `ExceedRetryLimitException` | 409 | `ExceedRetryLimitException()` | Превышен лимит повторных операций |
| `MigrationException` | 409 | `MigrationException()` | Ошибка миграции (перемещения) |
| `InternalLogicException` | 500 | `InternalLogicException(message: str)` | Внутренняя ошибка логики |

## Infra Exceptions

**File:** `src/infra/postgre/exceptions.py`

```
RepositoryException
├── IntegrityForeignException
├── IntegrityUniqueException
├── IntegrityUnknownException
└── InviteUniqueException
```

Инфра-исключения перехватываются в сервисном слое и оборачиваются в соответствующее `DomainException`:

| Infra Exception | Domain Wrapper | Condition |
|-----------------|----------------|-----------|
| `IntegrityForeignException` | `BadRequestException` | Нарушение внешнего ключа |
| `IntegrityUniqueException` | `BadRequestException` | Нарушение уникальности |
| `IntegrityUnknownException` | `InternalLogicException` | Неизвестная ошибка целостности |
| `InviteUniqueException` | `BadRequestException` | Дубликат приглашения |
