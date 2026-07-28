# GameRepository

**Protocol:** `src/core/interfaces/repo/game.py`
**Implementation:** `src/infra/postgre/repo/game.py`
**Model:** [Game](../models/game.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(game_id: UUID, /) -> Game \| None` | Поиск по первичному ключу |
| `delete` | `(game_id: UUID, /) -> bool` | Удаление по ID. Возвращает `True`, если запись была удалена |

## Custom Methods

### `get_by_name(name: str) -> Game | None`
Получает игру по названию. Использует `SELECT … WHERE name = :name LIMIT 1`.

### `get_all() -> Sequence[Game]`
Возвращает список всех игр без пагинации.

### `create(name: str, icon_id: UUID, banner_id: UUID) -> Game`
Создаёт новую игру. Добавляет `Game` в сессию, выполняет `flush` и повторно загружает запись через `get()`.

| Exception | Condition |
|-----------|-----------|
| `IntegrityUniqueException` | Игра с таким `name` уже существует (SQLSTATE 23505) |
| `IntegrityUnknownException` | Ошибка при создании |

### `set_name(game: Game, name: str) -> Game`
Устанавливает название игры. Модифицирует переданный ORM-объект и выполняет `flush`.

### `set_icon(game: Game, icon_id: UUID) -> Game`
Устанавливает иконку игры. Модифицирует переданный ORM-объект и выполняет `flush`.

### `set_banner(game: Game, banner_id: UUID) -> Game`
Устанавливает баннер игры. Модифицирует переданный ORM-объект и выполняет `flush`.

### `add_to_server(game_id: UUID, server_id: UUID) -> ServerGame`
Добавляет игру на сервер. Использует `INSERT … ON CONFLICT DO NOTHING` для избежания дубликатов. При конфликте возвращает существующую запись `ServerGame`.

| Exception | Condition |
|-----------|-----------|
| `IntegrityForeignException` | `game_id` или `server_id` не существует (SQLSTATE 23503) |
| `IntegrityUnknownException` | Непредвиденная ошибка |

### `remove_from_server(game_id: UUID, server_id: UUID) -> bool`
Удаляет игру с сервера. Использует `DELETE … WHERE game_id = :game_id AND server_id = :server_id`. Возвращает `True`, если удаление произошло.

### `bulk_add_to_server(server_id: UUID, game_ids: list[UUID]) -> list[ServerGame]`
Массово добавляет игры на сервер. Использует `INSERT … ON CONFLICT DO NOTHING` для всех `game_ids` в одном запросе.

| Exception | Condition |
|-----------|-----------|
| `IntegrityForeignException` | Некоторые `game_id` не существуют (SQLSTATE 23503) |
| `IntegrityUnknownException` | Непредвиденная ошибка |

### `bulk_remove_from_server(server_id: UUID, game_ids: list[UUID]) -> int`
Массово удаляет игры с сервера. Использует `DELETE … WHERE server_id = :server_id AND game_id IN :game_ids`. Возвращает количество удалённых записей.

### `set_server_games(server_id: UUID, game_ids: list[UUID]) -> None`
Устанавливает список игр сервера: вычисляет разницу между текущими и новыми `game_ids`, вызывает `bulk_add_to_server` для отсутствующих и `bulk_remove_from_server` для лишних.
