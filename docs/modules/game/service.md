# GameService — Business Logic

## Overview
- **File:** `src/core/services/game.py`

## Dependencies

### Repositories
- `GameRepositoryProtocol` — управление играми и связями с серверами
- `ServerRepositoryProtocol` — получение сервера

## Method: `list_server_games(server_id) -> list[Game]`

### Purpose
Возвращает список игр, добавленных на сервер.

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → `NotFoundException` если не найден
2. Вернуть `server.games`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

## Method: `add_games_to_server(server_id, game_ids, permission_mask) -> None`

### Purpose
Добавляет игры на сервер.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException` если недостаточно прав
2. Если `game_ids` пуст — досрочный возврат
3. Вызвать `game_repo.bulk_add_to_server(server_id, game_ids)`
4. `IntegrityForeignException` → `NotFoundException`
5. `IntegrityUniqueException` / `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Одна из игр не найдена (нарушение внешнего ключа) |
| `ForbiddenException` | Недостаточно прав |
| `InternalLogicException` | Ошибка целостности данных |

## Method: `remove_game_from_server(server_id, game_id, permission_mask) -> None`

### Purpose
Удаляет игру с сервера.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException` если недостаточно прав
2. Вызвать `game_repo.remove_from_server(game_id, server_id)`
3. Если `removed == False` → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена на сервере |
| `ForbiddenException` | Недостаточно прав |

## Method: `set_server_games(server_id, game_ids, permission_mask) -> None`

### Purpose
Устанавливает полный список игр сервера, заменяя существующий.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException` если недостаточно прав
2. Вызвать `game_repo.set_server_games(server_id, game_ids)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав |
