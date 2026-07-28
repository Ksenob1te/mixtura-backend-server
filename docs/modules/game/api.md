# Game — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/game.py`
- **Service file:** `src/core/services/game.py`
- **Commands file:** `src/core/commands/game.py`
- **Request models:** `src/app/rabbit/models/game.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `game.global.list` | *(нет)* | `list[GameDetailResponse]` | Список глобальных игр |
| `game.global.create` | `GlobalGameCreateRequest` | `GameDetailResponse` | Создание глобальной игры |
| `game.global.update` | `GlobalGameUpdateRequest` | `GameDetailResponse` | Обновление глобальной игры |
| `game.global.delete` | `GlobalGameDeleteRequest` | `StatusResponse` | Удаление глобальной игры |
| `game.server.list` | `GetServerGameListRequest` | `list[GameDetailResponse]` | Список игр, подключённых к серверу |
| `game.server.owned` | `GetOwnedGameListRequest` | `list[GameDetailResponse]` | Список локальных игр, принадлежащих серверу |
| `game.server.create` | `LocalGameCreateRequest` | `GameDetailResponse` | Создание локальной игры |
| `game.server.copy` | `LocalGameCopyRequest` | `GameDetailResponse` | Копирование глобальной игры в воркспейс |
| `game.server.update` | `LocalGameUpdateRequest` | `GameDetailResponse` | Обновление локальной игры |
| `game.server.delete` | `LocalGameDeleteRequest` | `StatusResponse` | Удаление локальной игры |
| `game.server.add` | `GameAddRequest` | `list[GameDetailResponse]` | Подключение игр к серверу |
| `game.server.remove` | `GameRemoveRequest` | `list[GameDetailResponse]` | Отключение игры от сервера |
| `game.server.set` | `GameSetRequest` | `list[GameDetailResponse]` | Установка полного списка подключённых игр |

Очереди `game.global.*` не принимают `access_data` и не проверяют права — авторизация обеспечивается gateway (только сайт-админ может публиковать в `*.global.*` очереди). Очереди `game.server.*` защищены `AccessDataRequest` (см. [_shared/access-data.md](../../_shared/access-data.md)); мутирующие из них проверяют право `EDIT_SERVER_GAME`.

---

## Queue: `game.global.list`

Обрабатывается `GameService.list_global_games()`.

### Command
Пустая команда (без полей).

### Result: `list[GameDetailResponse]`

**`GameDetailResponse`** (`src/app/rabbit/models/game.py`) — форма, которую возвращают все очереди `game.*`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `server_id` | `UUID \| None` | `None` — глобальная игра |
| `is_global` | `bool` | Вычисляется как `server_id is None` |
| `icon_id` | `UUID \| None` | |
| `banner_id` | `UUID \| None` | |
| `role_set` | `GameRoleSetResponse` | Набор ролей игры → полная схема в [game-role/api.md](../game-role/api.md) |
| `rating_set` | `RatingSetResponse` | Набор рейтингов игры → полная схема в [rating/api.md](../rating/api.md) |

### Exceptions
Нет.

---

## Queue: `game.global.create`

Обрабатывается `GameService.create_global_game()`.

### Command: `GlobalGameCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Название игры (максимум 128 символов) |
| `min_rating` | `int` | Yes | Минимальный рейтинг набора рейтингов |
| `max_rating` | `int` | Yes | Максимальный рейтинг набора рейтингов |
| `icon_id` | `UUID \| None` | No | |
| `banner_id` | `UUID \| None` | No | |

### Result: `GameDetailResponse`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Создаёт игру, набор ролей с единственной ролью «Leader» (`min_in_team = max_in_team = 1`) и набор рейтингов с переданными границами.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `BadRequestException` | `min_rating > max_rating`; название игры уже занято среди глобальных |
| `NotFoundException` | Нарушение внешнего ключа при создании |
| `InternalLogicException` | Ошибка целостности БД |

---

## Queue: `game.global.update`

Обрабатывается `GameService.update_global_game()`.

### Command: `GlobalGameUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_id` | `UUID` | Yes | Идентификатор игры |
| `name` | `str \| None` | No | Максимум 128 символов |
| `icon_id` | `UUID \| None` | No | |
| `banner_id` | `UUID \| None` | No | |

### Result: `GameDetailResponse`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Обновляет только переданные и отличающиеся от текущих поля.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена |
| `ForbiddenException` | `game_id` указывает на локальную игру |
| `BadRequestException` | Название игры уже занято среди глобальных |

---

## Queue: `game.global.delete`

Обрабатывается `GameService.delete_global_game()`.

### Command: `GlobalGameDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `game_id` | `UUID` | Yes | Идентификатор игры |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Behavior
- Каскадно удаляет `role_set`/`rating_set` игры (и вложенные роли/рейтинги).

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена |
| `ForbiddenException` | `game_id` указывает на локальную игру |
| `InternalLogicException` | Удаление не выполнено |

---

## Queue: `game.server.list`

Обрабатывается `GameService.list_server_games()`.

### Command: `GetServerGameListRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |

### Result: `list[GameDetailResponse]`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Возвращает игры, подключённые к серверу через `server_game` — как глобальные, так и локальные.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Queue: `game.server.owned`

Обрабатывается `GameService.list_owned_games()`.

### Command: `GetOwnedGameListRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |

### Result: `list[GameDetailResponse]`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Возвращает только локальные игры, принадлежащие серверу (`server_id` игры совпадает с сервером), независимо от того, подключены ли они через `server_game`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Queue: `game.server.create`

Обрабатывается `GameService.create_local_game()`.

### Command: `LocalGameCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `name` | `str` | Yes | Название игры (максимум 128 символов) |
| `min_rating` | `int` | Yes | |
| `max_rating` | `int` | Yes | |
| `icon_id` | `UUID \| None` | No | |
| `banner_id` | `UUID \| None` | No | |

### Result: `GameDetailResponse`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Создаёт локальную игру с ролью «Leader» и сразу подключает её к серверу.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_SERVER_GAME`) |
| `NotFoundException` | Сервер не найден |
| `BadRequestException` | `min_rating > max_rating`; название игры уже занято на сервере |

---

## Queue: `game.server.copy`

Обрабатывается `GameService.copy_global_game()`.

### Command: `LocalGameCopyRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_id` | `UUID` | Yes | Идентификатор глобальной игры-источника |

### Result: `GameDetailResponse`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Копирует глобальную игру как независимую локальную игру со всеми ролями и уровнями рейтинга исходной игры (без добавления дублирующей роли «Leader») и сразу подключает копию к серверу.
- Копия полностью независима от источника: последующие изменения глобальной игры её не затрагивают.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; `game_id` указывает на локальную (не глобальную) игру |
| `NotFoundException` | Сервер или исходная игра не найдены |
| `BadRequestException` | Название исходной игры уже занято локально на сервере |
| `InternalLogicException` | Копия не найдена после создания |

---

## Queue: `game.server.update`

Обрабатывается `GameService.update_local_game()`.

### Command: `LocalGameUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_id` | `UUID` | Yes | |
| `name` | `str \| None` | No | Максимум 128 символов |
| `icon_id` | `UUID \| None` | No | |
| `banner_id` | `UUID \| None` | No | |

### Result: `GameDetailResponse`
→ См. таблицу в контракте `game.global.list`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; `game_id` указывает на глобальную игру |
| `NotFoundException` | Игра не найдена; игра принадлежит другому серверу |
| `BadRequestException` | Название игры уже занято на сервере |

---

## Queue: `game.server.delete`

Обрабатывается `GameService.delete_local_game()`.

### Command: `LocalGameDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_id` | `UUID` | Yes | |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Behavior
- Каскадно удаляет `role_set`/`rating_set` локальной игры.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; игра глобальная |
| `NotFoundException` | Игра не найдена; принадлежит другому серверу |
| `InternalLogicException` | Удаление не выполнено |

---

## Queue: `game.server.add`

### Command: `GameAddRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_ids` | `list[UUID]` | Yes | ID подключаемых игр (глобальных и/или собственных локальных) |

### Result: `list[GameDetailResponse]`
Возвращает полный список игр сервера после добавления, включая вложенные `role_set`/`rating_set`. → См. таблицу в контракте `game.global.list`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Одна из игр не найдена или является локальной игрой другого сервера |
| `ForbiddenException` | Недостаточно прав (`EDIT_SERVER_GAME`) |

---

## Queue: `game.server.remove`

### Command: `GameRemoveRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_id` | `UUID` | Yes | ID отключаемой игры |

### Result: `list[GameDetailResponse]`
Возвращает полный список игр сервера после удаления. → См. таблицу в контракте `game.global.list`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена на сервере |
| `ForbiddenException` | Недостаточно прав |

---

## Queue: `game.server.set`

### Command: `GameSetRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `game_ids` | `list[UUID]` | Yes | Полный новый список подключённых игр |

### Result: `list[GameDetailResponse]`
→ См. таблицу в контракте `game.global.list`.

### Behavior
- Заменяет полный список подключённых игр сервера: добавляет новые, удаляет отсутствующие.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Одна из игр не найдена или является локальной игрой другого сервера |
| `ForbiddenException` | Недостаточно прав |
