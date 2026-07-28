# ServerRole

- **Pydantic file:** `src/core/models/server_role.py`
- **ORM file:** `src/infra/postgre/models/server_role.py`
- **Repo protocol:** `ServerRoleRepositoryProtocol`
- **Used by services:** `RoleService`, `MemberService`

## Role
Представляет роль на сервере. Каждая роль имеет уникальное в рамках сервера имя и позицию для сортировки.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `server_id` | `UUID` | ID сервера |
| `name` | `str` | Название роли |
| `position` | `int` | Позиция для сортировки |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server` | Сервер роли |
| `permissions` | `list[ServerRolePermission]` | Связи с правами через junction |
| `permissions_list` | `list[Permission]` | Права роли (many-to-many) |

## Create/Update Models

### Create — `ServerRoleCreate` (`src/core/models/server_role.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `server_id` | `UUID` | Yes | — | |
| `name` | `str` | Yes | — | Уникально в рамках сервера |
| `position` | `int` | No | `0` | |

### Update — `ServerRoleUpdate` (`src/core/models/server_role.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `position` | `int \| None` | No | `None` | |

> Поля `id`, `server_id` неизменяемы после создания.

### Read — `ServerRole` (`src/core/models/server_role.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `server_id` | `UUID` | |
| `name` | `str` | |
| `position` | `int` | |
| `permissions` | `list[ServerRolePermission]` | Навигационное свойство |
| `permissions_list` | `list[Permission]` | Навигационное свойство |
