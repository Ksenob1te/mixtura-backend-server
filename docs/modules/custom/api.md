# Custom — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/custom.py`
- **Service file:** `src/core/services/member_custom.py`
- **Commands file:** `src/core/commands/custom.py`
- **Request models:** `src/app/rabbit/models/custom.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `custom.get_by_member` | `GetCustomsRequest` | `list[CustomResponse]` | Кастомные списки участника |
| `custom.create` | `CreateCustomRequest` | `CustomResponse` | Создание кастомного списка |
| `custom.delete` | `DeleteCustomRequest` | `StatusResponse` | Удаление кастомного списка |
| `custom.rating.set` | `UpdateGameRoleRatingRequest` | `CustomResponse` | Установка оценки роли |

---

## Queue: `custom.get_by_member`

### Command: `GetCustomsRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID участника |

### Result: `list[CustomResponse]`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `member` | `ReducedMemberResponse` | Владелец списка |
| `creator` | `ReducedMemberResponse` | Создатель списка |
| `custom_ratings` | `list[CustomRatingResponse]` | Оценки ролей |

**`ReducedMemberResponse`:**
| Field | Type |
|-------|------|
| `id` | `UUID` |
| `nickname` | `str` |
| `user_id` | `UUID \| None` |

**`GameRoleItemResponse`:**
| Field | Type |
|-------|------|
| `id` | `UUID` |
| `name` | `str` |
| `icon_id` | `UUID \| None` |
| `min_in_team` | `int` |
| `max_in_team` | `int` |
| `hidden` | `bool` |

**`CustomRatingResponse`:**
| Field | Type | Description |
|-------|------|-------------|
| `game_role` | `GameRoleItemResponse` | Игровая роль |
| `rating` | `int` | Оценка |

---

## Queue: `custom.create`

### Command: `CreateCustomRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID участника-владельца списка |

### Result: `CustomResponse`

Поля — см. [Queue: `custom.get_by_member`](#queue-customget_by_member).

### Behavior
- Если `access_data.member_id` не указан — выбрасывает `NotFoundException`.
- Создаёт пустой кастомный список (без оценок) для целевого участника.
- Поле `creator` устанавливается в участника, указанного в `access_data.member_id`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | `access_data.member_id` отсутствует; целевой участник не найден; issuer (создатель) не найден в БД |
| `ForbiddenException` | Недостаточно прав (требуется `CREATE_CUSTOM`) |
| `InternalLogicException` | Ошибка создания записи в БД |

---

## Queue: `custom.delete`

### Command: `DeleteCustomRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `custom_id` | `UUID` | Yes | ID кастомного списка |

### Result: `StatusResponse`
| Field | Type | Description |
|-------|------|-------------|
| `status` | `str` | Всегда `"ok"` |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник из `access_data` не найден; кастомный список не найден |
| `ForbiddenException` | Недостаточно прав (требуется `DELETE_CUSTOM`) |

---

## Queue: `custom.rating.set`

### Command: `UpdateGameRoleRatingRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `custom_id` | `UUID` | Yes | ID кастомного списка |
| `game_role_id` | `UUID` | Yes | ID игровой роли |
| `rating` | `int` | Yes | Оценка |

### Result: `CustomResponse`

Поля — см. [Queue: `custom.get_by_member`](#queue-customget_by_member).

### Behavior
- Проверяет, что игровая роль (`game_role_id`) принадлежит игре, подключённой к серверу участника (`game_repo.is_enabled_on_server`).
- Проверяет, что оценка находится в пределах `[min_rating, max_rating]` набора рейтингов **игры**, которой принадлежит `game_role_id` (не сервера) — границы у разных игр на одном сервере могут отличаться.
- Если запись оценки для пары `(custom_id, game_role_id)` существует — обновляет существующую.
- Если не существует — создаёт новую запись `CustomRating`.
- Редактировать оценки может создатель кастомного списка **или** участник с правом `EDIT_ALL_CUSTOMS`.
- Один `Custom` не привязан к одной игре: может хранить оценки ролей из разных игр, подключённых к серверу.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Кастомный список не найден; `game_role_id` не найден в БД; игра роли не подключена к серверу участника |
| `ForbiddenException` | Участник не является создателем списка и не имеет права `EDIT_ALL_CUSTOMS` |
| `BadRequestException` | Значение `rating` выходит за пределы `[min_rating, max_rating]`, заданные набором рейтингов игры, которой принадлежит `game_role_id` |
| `InternalLogicException` | Участник или сервер для custom не найдены; набор ролей или набор рейтингов игры не найдены; нарушение уникальности при создании оценки |
