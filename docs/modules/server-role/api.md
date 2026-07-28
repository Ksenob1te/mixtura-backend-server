# Server Role — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/server_role.py`
- **Service file:** `src/core/services/role.py`
- **Commands file:** `src/core/commands/role.py`
- **Request models:** `src/app/rabbit/models/role.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `server.global.permissions` | *(нет)* | `list[PermissionResponse]` | Глобальные типы прав |
| `server.role.list` | `ListServerRolesRequest` | `list[ServerRoleResponse]` | Список ролей сервера |
| `server.role.create` | `CreateServerRoleRequest` | `ServerRoleResponse` | Создание роли |
| `server.role.update` | `UpdateServerRoleRequest` | `ServerRoleResponse` | Обновление роли |
| `server.role.permissions.update` | `UpdateServerRolePermissionsRequest` | `ServerRoleResponse` | Обновление прав роли |
| `server.role.delete` | `DeleteServerRoleRequest` | `StatusResponse` | Удаление роли |

---

## Queue: `server.global.permissions`

Незащищённый эндпоинт — не требует `access_data`.

### Command: Пустая команда (без полей).

### Result: `list[PermissionResponse]`
→ См. [_shared/response-wrapper.md](../../_shared/response-wrapper.md) для конверта.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ID права |
| `code` | `str` | Код права |

### Behavior
- Возвращает все глобально определённые типы прав из `PERMISSION` StrEnum
- Используется UI для отображения доступных прав при настройке ролей

---

## Queue: `server.role.list`

### Command: `ListServerRolesRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |

### Result: `list[ServerRoleResponse]`

**ServerRoleResponse:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | Название роли |
| `position` | `int` | Позиция роли (порядок сортировки) |
| `permissions_list` | `list[PermissionResponse]` | Права, назначенные роли |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Queue: `server.role.create`

### Command: `CreateServerRoleRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `name` | `str` | Yes | Название роли |
| `position` | `int` | Yes | Позиция роли |

### Result: `ServerRoleResponse`
→ Как в `server.role.list`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден (указан несуществующий `server_id`) |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_SERVER_ROLES`) |
| `InternalLogicException` | Ошибка целостности данных |

---

## Queue: `server.role.update`

### Command: `UpdateServerRoleRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `role_id` | `UUID` | Yes | ID роли |
| `name` | `str \| None` | No | Новое название |
| `position` | `int \| None` | No | Новая позиция |

### Result: `ServerRoleResponse`
→ Как в `server.role.list`.

### Behavior
- Обновляются только переданные поля (не `None`)
- Роль должна принадлежать указанному серверу

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_SERVER_ROLES`) |

---

## Queue: `server.role.permissions.update`

### Command: `UpdateServerRolePermissionsRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `role_id` | `UUID` | Yes | ID роли |
| `target_permissions_ids` | `list[UUID]` | Yes | ID прав для назначения (полная замена набора) |

### Result: `ServerRoleResponse`
→ Как в `server.role.list`.

### Behavior
- Полная замена набора прав роли, а не добавление/удаление отдельных
- Роль должна принадлежать указанному серверу

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены; указан несуществующий `permission_id` |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_SERVER_ROLES`) |
| `InternalLogicException` | Ошибка целостности данных |

---

## Queue: `server.role.delete`

### Command: `DeleteServerRoleRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `role_id` | `UUID` | Yes | ID роли |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_SERVER_ROLES`) |
