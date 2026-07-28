# GameRoleSet

- **Pydantic file:** `src/core/models/game_role_set.py`
- **ORM file:** `src/infra/postgre/models/game_role_set.py`
- **Repo protocol:** `GameRoleSetRepositoryProtocol`
- **Used by services:** `GameService`, `GameRoleService`, `MemberCustomService`

## Role
Набор ролей, принадлежащий ровно одной игре (`Game`). Игра владеет своим набором ролей 1:1 — набор создаётся вместе с игрой и каскадно удаляется вместе с ней.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название набора |
| `game_id` | `UUID` | ID игры-владельца (уникально — один набор ролей на игру) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `game` | `Game` | Игра-владелец набора |
| `game_roles` | `list[GameRole]` | Роли в наборе |

## Create/Update Models

### Create — `GameRoleSetCreate` (`src/core/models/game_role_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `game_id` | `UUID` | Yes | — | |

### Update — `GameRoleSetUpdate` (`src/core/models/game_role_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |

> Поля `id` и `game_id` неизменяемы после создания.

### Read — `GameRoleSet` (`src/core/models/game_role_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `game_id` | `UUID` | |

#### `GameRoleSetDetail` (`src/core/models/game_role_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| *(поля `GameRoleSet`)* | | |
| `game_roles` | `list[GameRole]` | Навигационное свойство |
