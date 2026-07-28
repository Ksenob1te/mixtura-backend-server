# Game — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/game.py`
- **Service file:** `src/core/services/game.py`
- **Commands file:** `src/core/commands/game.py`
- **Request models:** `src/app/rabbit/models/game.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `server.global.games` | *(нет)* | `list[GameResponse]` | Глобальные игры |
| `game.server.add` | `GameAddRequest` | `list[GameResponse]` | Добавление игр на сервер |
| `game.server.remove` | `GameRemoveRequest` | `list[GameResponse]` | Удаление игры с сервера |
| `game.server.set` | `GameSetRequest` | `list[GameResponse]` | Установка списка игр сервера |
| `game.server.list` | `GetServerGameListRequest` | `list[GameResponse]` | Список игр сервера |

---

## Queue: `server.global.games`

### Command: Пустая команда (без полей).

### Result: `list[GameResponse]`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `icon_id` | `UUID` | |
| `banner_id` | `UUID` | |

---

## Queue: `game.server.add`

### Command: `GameAddRequest` (`src/app/rabbit/models/game.py`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | См. [_shared/access-data.md](../../_shared/access-data.md) |
| `game_ids` | `list[UUID]` | Yes | ID добавляемых игр |

### Result: `list[GameResponse]`

Результат возвращает полный список игр сервера после добавления. См. [GameResponse](#queue-serverglobalgames) (описание полей).

### Behavior
- Возвращает полный список игр сервера после добавления

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена |
| `ForbiddenException` | Недостаточно прав (`EDIT_SERVER_GAME`) |

---

## Queue: `game.server.remove`

### Command: `GameRemoveRequest` (`src/app/rabbit/models/game.py`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | См. [_shared/access-data.md](../../_shared/access-data.md) |
| `game_id` | `UUID` | Yes | ID удаляемой игры |

### Result: `list[GameResponse]`

Результат возвращает полный список игр сервера после удаления. См. [GameResponse](#queue-serverglobalgames) (описание полей).

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена на сервере |
| `ForbiddenException` | Недостаточно прав |

---

## Queue: `game.server.set`

### Command: `GameSetRequest` (`src/app/rabbit/models/game.py`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | См. [_shared/access-data.md](../../_shared/access-data.md) |
| `game_ids` | `list[UUID]` | Yes | ID игр для установки |

### Result: `list[GameResponse]`

См. [GameResponse](#queue-serverglobalgames) (описание полей).

### Behavior
- Заменяет полный список игр сервера: добавляет новые, удаляет отсутствующие

---

## Queue: `game.server.list`

### Command: `GetServerGameListRequest` (`src/app/rabbit/models/game.py`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | См. [_shared/access-data.md](../../_shared/access-data.md) |

### Result: `list[GameResponse]`

См. [GameResponse](#queue-serverglobalgames) (описание полей).
