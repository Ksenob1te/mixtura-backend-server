# GameRepository

**Protocol:** `src/core/interfaces/repo/game.py`
**Implementation:** `src/infra/postgre/repo/game.py`
**Model:** [Game](../models/game.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(game_id: UUID, /) -> Game \| None` | Поиск по первичному ключу. Возвращает плоский `Game`, без вложенных наборов |
| `delete` | `(game_id: UUID, /) -> bool` | Удаление по ID. Возвращает `True`, если запись была удалена |

## Custom Methods

### `get_by_name`

```python
async def get_by_name(self, name: str, server_id: UUID | None = None) -> Game | None
```

Получает игру по названию в пределах области видимости: если `server_id` не передан — ищет среди глобальных игр (`server_id IS NULL`), иначе — среди локальных игр указанного сервера.

### `get_detail`

```python
async def get_detail(self, game_id: UUID) -> GameDetail | None
```

Получает игру вместе с вложенными `role_set` и `rating_set`. Все связи загружаются `lazy="selectin"`, поэтому дополнительные `options` не требуются.

### `list_global`

```python
async def list_global(self) -> Sequence[GameDetail]
```

Список всех глобальных игр (`server_id IS NULL`) с вложенными наборами.

### `list_owned_by_server`

```python
async def list_owned_by_server(self, server_id: UUID) -> Sequence[GameDetail]
```

Список локальных игр, принадлежащих указанному серверу (`server_id = :server_id`), с вложенными наборами.

### `list_for_server`

```python
async def list_for_server(self, server_id: UUID) -> Sequence[GameDetail]
```

Список игр, подключённых к серверу через `ServerGame` (и глобальные, и локальные), с вложенными наборами. Выполняет `JOIN` с `server_game`.

### `is_enabled_on_server`

```python
async def is_enabled_on_server(self, server_id: UUID, game_id: UUID) -> bool
```

Проверяет, подключена ли игра к серверу (наличие строки в `server_game`).

### `create`

```python
async def create(self, dto: GameCreate) -> Game
```

Создаёт новую игру.

| Exception | Condition |
|-----------|-----------|
| `IntegrityUniqueException` | Нарушение уникальности имени в области видимости (SQLSTATE 23505) — `uq_game_server_name` или частичный индекс `uq_game_global_name` |
| `IntegrityForeignException` | `server_id` не существует (SQLSTATE 23503) |
| `IntegrityUnknownException` | Другая ошибка целостности |

### `add_to_server`

```python
async def add_to_server(self, game_id: UUID, server_id: UUID) -> ServerGame
```

Добавляет игру на сервер. Использует `INSERT … ON CONFLICT DO NOTHING` для избежания дубликатов. При конфликте возвращает существующую запись `ServerGame`.

| Exception | Condition |
|-----------|-----------|
| `IntegrityForeignException` | `game_id` или `server_id` не существует (SQLSTATE 23503) |
| `IntegrityUnknownException` | Непредвиденная ошибка |

### `remove_from_server`

```python
async def remove_from_server(self, game_id: UUID, server_id: UUID) -> bool
```

Удаляет игру с сервера. Использует `DELETE … WHERE game_id = :game_id AND server_id = :server_id`. Возвращает `True`, если удаление произошло.

### `bulk_add_to_server`

```python
async def bulk_add_to_server(self, server_id: UUID, game_ids: list[UUID]) -> list[ServerGame]
```

Массово добавляет игры на сервер. Использует `INSERT … ON CONFLICT DO NOTHING` для всех `game_ids` в одном запросе.

| Exception | Condition |
|-----------|-----------|
| `IntegrityForeignException` | Некоторые `game_id` не существуют (SQLSTATE 23503) |
| `IntegrityUnknownException` | Непредвиденная ошибка |

### `bulk_remove_from_server`

```python
async def bulk_remove_from_server(self, server_id: UUID, game_ids: list[UUID]) -> int
```

Массово удаляет игры с сервера. Использует `DELETE … WHERE server_id = :server_id AND game_id IN :game_ids`. Возвращает количество удалённых записей.

### `set_server_games`

```python
async def set_server_games(self, server_id: UUID, game_ids: list[UUID]) -> None
```

Устанавливает список игр сервера: вычисляет разницу между текущими и новыми `game_ids`, вызывает `bulk_add_to_server` для отсутствующих и `bulk_remove_from_server` для лишних.
