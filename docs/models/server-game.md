# ServerGame

- **Pydantic file:** `src/core/models/server_game.py`
- **ORM file:** `src/infra/postgre/models/server_game.py`
- **Repo protocol:** — (используется через GameRepository)
- **Used by services:** `GameService`

## Role
Junction-модель для связи многие-ко-многим между серверами и играми. Не имеет собственных DTO create/update.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `server_id` | `UUID` | ID сервера (PK, FK → Server) |
| `game_id` | `UUID` | ID игры (PK, FK → Game) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server` | Сервер |
| `game` | `Game` | Игра |

> ServerGame — чистая junction-модель без собственного поля `id` в Pydantic (в ORM есть `id`). Не имеет Create/Update/Read DTO. Создаётся и удаляется через методы GameRepository.
