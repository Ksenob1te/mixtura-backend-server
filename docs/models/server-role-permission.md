# ServerRolePermission

- **ORM file:** `src/infra/postgre/models/server_role_permission.py`
- **Repo protocol:** — (управляется через `PermissionRepository`)
- **Used by services:** `RoleService`

## Role
Junction-модель для связи многие-ко-многим между ролями сервера и правами доступа.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `server_role_id` | `UUID` | ID роли сервера (FK → ServerRole) |
| `permission_id` | `UUID` | ID права (FK → Permission) |

## Constraints

- Unique: `(server_role_id, permission_id)` — каждая пара уникальна
- CASCADE on delete для `server_role_id` и `permission_id`

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server_role` | `ServerRole` | Роль сервера |
| `permission` | `Permission` | Право доступа |

> ServerRolePermission — ORM junction модель, не имеет Pydantic представления и DTO. Управляется через методы `PermissionRepository` (`assign_to_role`, `remove_from_role`, `bulk_set_for_role`).
