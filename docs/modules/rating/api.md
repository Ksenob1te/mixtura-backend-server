# Rating — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/rating.py`
- **Service file:** `src/core/services/rating.py`
- **Commands file:** `src/core/commands/rating.py`
- **Request models:** `src/app/rabbit/models/rating.py`

Очереди `rating_set.*` защищены `AccessDataRequest` (см. [_shared/access-data.md](../../_shared/access-data.md)) и требуют право `EDIT_RATING_SET`, применимое к набору рейтингов **локальной** игры сервера. Очереди `rating_set.global.*` не принимают `access_data` и не проверяют права — авторизация обеспечивается gateway; они действуют на набор рейтингов **глобальной** игры.

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `rating_set.update` | `RatingSetUpdateRequest` | `RatingSetResponse` | Обновление набора рейтингов локальной игры |
| `rating_set.rating.create` | `RatingItemCreateRequest` | `RatingItemResponse` | Создание уровня рейтинга локальной игры |
| `rating_set.rating.update` | `RatingItemUpdateRequest` | `RatingItemResponse` | Обновление уровня рейтинга локальной игры |
| `rating_set.rating.icon.delete` | `RatingItemDeleteRequest` | `StatusResponse` | Удаление иконки уровня рейтинга локальной игры |
| `rating_set.rating.delete` | `RatingItemDeleteRequest` | `StatusResponse` | Удаление уровня рейтинга локальной игры |
| `rating_set.global.update` | `GlobalRatingSetUpdateRequest` | `RatingSetResponse` | Обновление набора рейтингов глобальной игры |
| `rating_set.global.rating.create` | `GlobalRatingCreateRequest` | `RatingItemResponse` | Создание уровня рейтинга глобальной игры |
| `rating_set.global.rating.update` | `GlobalRatingUpdateRequest` | `RatingItemResponse` | Обновление уровня рейтинга глобальной игры |
| `rating_set.global.rating.icon.delete` | `GlobalRatingDeleteRequest` | `StatusResponse` | Удаление иконки уровня рейтинга глобальной игры |
| `rating_set.global.rating.delete` | `GlobalRatingDeleteRequest` | `StatusResponse` | Удаление уровня рейтинга глобальной игры |

> Отдельной очереди для чтения набора рейтингов больше нет — набор всегда доставляется вложенным внутри `GameDetailResponse` (см. [game/api.md](../game/api.md)).

---

## Queue: `rating_set.update`

Обрабатывается `RatingService.update_rating_set()`.

### Command: `RatingSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `rating_set_id` | `UUID` | Yes | Идентификатор набора рейтингов |
| `name` | `str \| None` | No | Максимум 32 символа |
| `min_rating` | `int \| None` | No | |
| `max_rating` | `int \| None` | No | |

### Result: `RatingSetResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `game_id` | `UUID` | ID игры-владельца набора |
| `min_rating` | `int` | |
| `max_rating` | `int` | |
| `ratings` | `list[RatingItemResponse]` | Уровни рейтинга (см. ниже) |

**`RatingItemResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `threshold` | `int` | Пороговое значение |
| `icon_id` | `UUID \| None` | Идентификатор иконки |

### Behavior
1. Проверка прав `EDIT_RATING_SET`.
2. Проверка, что `rating_set_id` принадлежит набору рейтингов локальной игры сервера.
3. Собрать изменившиеся поля (`name`, `min_rating`, `max_rating`); проверить эффективные границы (`min_rating <= max_rating` с учётом обновляемых значений).
4. Обновить, если есть изменения.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу |
| `BadRequestException` | Эффективные `min_rating` > `max_rating` |

---

## Queue: `rating_set.global.update`

Обрабатывается `RatingService.update_global_rating_set()`. Не требует `access_data`.

### Command: `GlobalRatingSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating_set_id` | `UUID` | Yes | |
| `name` | `str \| None` | No | Максимум 32 символа |
| `min_rating` | `int \| None` | No | |
| `max_rating` | `int \| None` | No | |

### Result: `RatingSetResponse`
→ См. таблицу в контракте `rating_set.update`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден |
| `BadRequestException` | Эффективные `min_rating` > `max_rating` |

---

## Queue: `rating_set.rating.create`

Обрабатывается `RatingService.create_rating()`.

### Command: `RatingItemCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `rating_set_id` | `UUID` | Yes | |
| `threshold` | `int` | Yes | Пороговое значение уровня |
| `icon_id` | `UUID \| None` | No | |

### Result: `RatingItemResponse`
→ См. таблицу в контракте `rating_set.update`.

### Behavior
- Создаёт новый уровень рейтинга в наборе.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Queue: `rating_set.global.rating.create`

Обрабатывается `RatingService.create_global_rating()`. Не требует `access_data`.

### Command: `GlobalRatingCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating_set_id` | `UUID` | Yes | |
| `threshold` | `int` | Yes | |
| `icon_id` | `UUID \| None` | No | |

### Result: `RatingItemResponse`
→ См. таблицу в контракте `rating_set.update`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Queue: `rating_set.rating.update`

Обрабатывается `RatingService.update_rating()`.

### Command: `RatingItemUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `rating_item_id` | `UUID` | Yes | |
| `threshold` | `int \| None` | No | |
| `icon_id` | `UUID \| None` | No | |

### Result: `RatingItemResponse`
→ См. таблицу в контракте `rating_set.update`.

### Behavior
- Обновляет только переданные и изменившиеся поля.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу |

---

## Queue: `rating_set.global.rating.update`

Обрабатывается `RatingService.update_global_rating()`. Не требует `access_data`.

### Command: `GlobalRatingUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating_item_id` | `UUID` | Yes | |
| `threshold` | `int \| None` | No | |
| `icon_id` | `UUID \| None` | No | |

### Result: `RatingItemResponse`
→ См. таблицу в контракте `rating_set.update`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден |

---

## Queue: `rating_set.rating.icon.delete`

Обрабатывается `RatingService.delete_rating_icon()`. Удаляет иконку уровня рейтинга (устанавливает `icon_id` в `None`).

### Command: `RatingItemDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `rating_item_id` | `UUID` | Yes | |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу |

---

## Queue: `rating_set.global.rating.icon.delete`

Обрабатывается `RatingService.delete_global_rating_icon()`. Не требует `access_data`.

### Command: `GlobalRatingDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating_item_id` | `UUID` | Yes | |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден |

---

## Queue: `rating_set.rating.delete`

Обрабатывается `RatingService.delete_rating()`. Удаляет уровень рейтинга.

### Command: `RatingItemDeleteRequest`
→ См. таблицу в контракте `rating_set.rating.icon.delete`.

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу |

---

## Queue: `rating_set.global.rating.delete`

Обрабатывается `RatingService.delete_global_rating()`. Не требует `access_data`.

### Command: `GlobalRatingDeleteRequest`
→ См. таблицу в контракте `rating_set.global.rating.icon.delete`.

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден |
