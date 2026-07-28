# Permission

- **Pydantic file:** `src/core/models/permission.py`
- **ORM file:** `src/infra/postgre/models/permission.py`
- **Repo protocol:** `PermissionRepositoryProtocol`
- **Used by services:** `CoreService`, `AccessControlService`, `RoleService`

## Role
Представляет право доступа в системе. Статические записи, создаваемые при инициализации из `PERMISSION` StrEnum (см. [_shared/permission-bits.md](../_shared/permission-bits.md)).

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `code` | `str` | Код права (из PERMISSION StrEnum) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `roles` | `list[ServerRole]` | Роли, которым назначено право (many-to-many через ServerRolePermission) |

## Create/Update Models

### Create — `PermissionCreate` (`src/core/models/permission.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `code` | `str` | Yes | — | Код права |

> Права не имеют Update-модели. Поля `id` и `code` неизменяемы после создания.

### Read — `Permission` (`src/core/models/permission.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `code` | `str` | |
