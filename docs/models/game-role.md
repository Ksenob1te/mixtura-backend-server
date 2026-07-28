# GameRole

- **Pydantic file:** `src/core/models/game_role.py`
- **ORM file:** `src/infra/postgre/models/game_role.py`
- **Repo protocol:** `GameRoleRepositoryProtocol`
- **Used by services:** `GameRoleService`, `MemberCustomService`

## Role
Представляет роль в игровом наборе ролей. Определяет минимальное и максимальное количество участников в команде для данной роли.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название роли |
| `role_set_id` | `UUID` | ID набора ролей |
| `icon_id` | `UUID \| None` | ID иконки |
| `min_in_team` | `int` | Минимум участников в команде |
| `max_in_team` | `int` | Максимум участников в команде |
| `hidden` | `bool` | Флаг скрытия роли |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `role_set` | `GameRoleSet` | Набор ролей |

## Create/Update Models

### Create — `GameRoleCreate` (`src/core/models/game_role.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `role_set_id` | `UUID` | Yes | — | |
| `min_in_team` | `int` | Yes | — | |
| `max_in_team` | `int` | Yes | — | |
| `icon_id` | `UUID \| None` | No | `None` | |
| `hidden` | `bool` | No | `False` | |

### Update — `GameRoleUpdate` (`src/core/models/game_role.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `min_in_team` | `int \| None` | No | `None` | |
| `max_in_team` | `int \| None` | No | `None` | |
| `icon_id` | `UUID \| None` | No | `None` | |
| `hidden` | `bool \| None` | No | `None` | |

> Поля `id`, `role_set_id` неизменяемы после создания.

### Read — `GameRole` (`src/core/models/game_role.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `role_set_id` | `UUID` | |
| `icon_id` | `UUID \| None` | |
| `min_in_team` | `int` | |
| `max_in_team` | `int` | |
| `hidden` | `bool` | |
