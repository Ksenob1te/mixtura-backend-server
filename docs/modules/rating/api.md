# Rating — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/rating.py`
- **Service file:** `src/core/services/rating.py`
- **Commands file:** `src/core/commands/rating.py`
- **Request models:** `src/app/rabbit/models/rating.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `rating_set.get_global` | *(пустая команда)* | `list[RatingSetResponse]` | Глобальные шаблоны рейтингов |
| `rating_set.get_by_server` | `GetServerRatingSetsRequest` | `RatingSetResponse` | Набор рейтингов сервера |
| `rating_set.update` | `RatingSetUpdateRequest` | `RatingSetResponse` | Обновление набора рейтингов |
| `rating_set.rating.create` | `RatingItemCreateRequest` | `RatingItemResponse` | Создание уровня рейтинга |
| `rating_set.rating.update` | `RatingItemUpdateRequest` | `RatingItemResponse` | Обновление уровня рейтинга |
| `rating_set.rating.delete` | `RatingItemDeleteRequest` | `StatusResponse` | Удаление уровня рейтинга |

---

## Queue: `rating_set.get_global`

Обрабатывается через `CoreService.get_global_rating_templates()`.

### Command
Пустая команда (без полей).

### Result: `list[RatingSetResponse]`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор набора |
| `name` | `str` | Название набора |
| `min_rating` | `int` | Минимальное значение рейтинга |
| `max_rating` | `int` | Максимальное значение рейтинга |
| `is_global` | `bool` | Флаг глобального шаблона |
| `ratings` | `list[RatingItemResponse]` | Уровни рейтинга (см. ниже) |

**RatingItemResponse:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор уровня |
| `threshold` | `int` | Пороговое значение |
| `icon_id` | `UUID` | Идентификатор иконки |

### Exceptions
Нет.

---

## Queue: `rating_set.get_by_server`

### Command: `GetServerRatingSetsRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации ([_shared/access-data.md](../../_shared/access-data.md)) |

### Result: `RatingSetResponse`

→ См. полную таблицу в контракте `rating_set.get_global`.

### Behavior
- Возвращает `RatingSet`, привязанный к серверу через `server.rating_set`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Queue: `rating_set.update`

### Command: `RatingSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации ([_shared/access-data.md](../../_shared/access-data.md)) |
| `rating_set_id` | `UUID` | Yes | Идентификатор набора рейтингов |
| `name` | `str \| None` | No | Название (максимум 32 символа) |
| `min_rating` | `int \| None` | No | Минимальное значение рейтинга |
| `max_rating` | `int \| None` | No | Максимальное значение рейтинга |

### Result: `RatingSetResponse`

→ См. полную таблицу в контракте `rating_set.get_global`.

### Behavior
- Обновляет только переданные поля (`name`, `min_rating`, `max_rating`). Поля со значением `None` не изменяются.
- Проверяет, что `rating_set_id` принадлежит указанному серверу.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_RATING_SET`) |
| `NotFoundException` | Набор рейтингов не найден для сервера |

---

## Queue: `rating_set.rating.create`

### Command: `RatingItemCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации ([_shared/access-data.md](../../_shared/access-data.md)) |
| `rating_set_id` | `UUID` | Yes | Идентификатор набора рейтингов |
| `threshold` | `int` | Yes | Пороговое значение уровня |
| `icon_id` | `UUID \| None` | No | Идентификатор иконки |

### Result: `RatingItemResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор уровня |
| `threshold` | `int` | Пороговое значение |
| `icon_id` | `UUID` | Идентификатор иконки |

### Behavior
- Создаёт новый уровень рейтинга и добавляет его в список `ratings` набора.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_RATING_SET`) |
| `NotFoundException` | Набор рейтингов не найден для сервера; связанная сущность не найдена (`IntegrityForeignException`) |
| `InternalLogicException` | Непредвиденная ошибка целостности (`IntegrityUnknownException`) |

---

## Queue: `rating_set.rating.update`

### Command: `RatingItemUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации ([_shared/access-data.md](../../_shared/access-data.md)) |
| `rating_item_id` | `UUID` | Yes | Идентификатор уровня рейтинга |
| `threshold` | `int \| None` | No | Пороговое значение |
| `icon_id` | `UUID \| None` | No | Идентификатор иконки |

### Result: `RatingItemResponse`

→ См. полную таблицу в контракте `rating_set.rating.create`.

### Behavior
- Обновляет только переданные поля. Поля со значением `None` не изменяются.
- Проверяет, что уровень рейтинга принадлежит указанному серверу.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_RATING_SET`) |
| `NotFoundException` | Уровень рейтинга не найден; уровень не принадлежит серверу |

---

## Queue: `rating_set.rating.delete`

### Command: `RatingItemDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации ([_shared/access-data.md](../../_shared/access-data.md)) |
| `rating_item_id` | `UUID` | Yes | Идентификатор уровня рейтинга |

### Result: `StatusResponse`

→ См. [_shared/response-wrapper.md](../../_shared/response-wrapper.md). Поле `status` = `"ok"`.

### Behavior
- Удаляет уровень рейтинга. Проверяет принадлежность серверу через `_check_rating`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_RATING_SET`) |
| `NotFoundException` | Уровень рейтинга не найден; уровень не принадлежит серверу |
