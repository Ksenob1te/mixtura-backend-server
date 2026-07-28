# GameRoleSet

- **Pydantic file:** `src/core/models/game_role_set.py`
- **ORM file:** `src/infra/postgre/models/game_role_set.py`
- **Repo protocol:** `GameRoleSetRepositoryProtocol`
- **Used by services:** `CoreService`, `GameRoleService`

## Role
Представляет набор ролей для игры. Может быть глобальным шаблоном или принадлежать конкретному серверу.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название набора |
| `is_global` | `bool` | Флаг глобального шаблона |
| `server_id` | `UUID \| None` | ID сервера (если не глобальный) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server \| None` | Сервер набора |
| `game_roles` | `list[GameRole]` | Роли в наборе |

## Create/Update Models

### Create — `GameRoleSetCreate` (`src/core/models/game_role_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `is_global` | `bool` | No | `False` | |
| `server_id` | `UUID \| None` | No | `None` | |

### Update — `GameRoleSetUpdate` (`src/core/models/game_role_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |

> Поля `id`, `is_global`, `server_id` неизменяемы после создания.

### Read — `GameRoleSet` (`src/core/models/game_role_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `is_global` | `bool` | |
| `server_id` | `UUID \| None` | |
