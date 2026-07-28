# RoleService — Business Logic

## Overview
- **File:** `src/core/services/role.py`

## Dependencies

### Repositories
- `ServerRepositoryProtocol` — получение сервера для проверки владельца
- `ServerRoleRepositoryProtocol` — CRUD ролей сервера
- `MemberRepositoryProtocol` — получение участника для проверки прав
- `PermissionRepositoryProtocol` — управление правами ролей

## Method: `list_roles(server_id: UUID) -> list[ServerRole]`

### Purpose
Возвращает список ролей сервера, отсортированный по позиции.

### Algorithm
1. Получить сервер по `server_id` → `NotFoundException` если не найден
2. Вызвать `role_repo.list_for_server(server_id)`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Сервер не найден|

## Method: `create_role(server_id: UUID, name: str, position: int, permission_mask: int) -> ServerRole`

### Purpose
Создаёт новую роль на сервере.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission через `access_control_service` → `ForbiddenException` если недостаточно прав
2. Получить сервер по `server_id` → `NotFoundException` если не найден
3. Вызвать `role_repo.create(server_id, name, position)`
4. Перехватить `IntegrityForeignException` → `NotFoundException`; `IntegrityUniqueException` → `InternalLogicException`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Сервер не найден; `server_id` ссылается на несуществующий сервер|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|
|`InternalLogicException`|Дубликат имени роли на сервере|

## Method: `update_role(server_id: UUID, role_id: UUID, name: str | None, position: int | None, permission_mask: int) -> ServerRole`

### Purpose
Обновляет название и/или позицию роли.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission → `ForbiddenException` если недостаточно прав
2. Получить сервер по `server_id` → `NotFoundException` если не найден
3. Получить роль по `role_id` → `NotFoundException` если не найдена
4. Если `name` указан: вызвать `role_repo.set_name(role_id, name)`
5. Если `position` указан: вызвать `role_repo.set_position(role_id, position)`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Сервер или роль не найдены|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|

## Method: `add_permission(server_id: UUID, role_id: UUID, permission_id: UUID, permission_mask: int) -> ServerRole`

### Purpose
Добавляет отдельное право к роли.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission → `ForbiddenException` если недостаточно прав
2. Получить роль по `role_id` → `NotFoundException` если не найдена
3. Вызвать `permission_repo.assign_to_role(permission_id, role_id)`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Роль или право не найдены|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|

## Method: `remove_permission(server_id: UUID, role_id: UUID, permission_id: UUID, permission_mask: int) -> ServerRole`

### Purpose
Отзывает отдельное право у роли.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission → `ForbiddenException` если недостаточно прав
2. Получить роль по `role_id` → `NotFoundException` если не найдена
3. Вызвать `permission_repo.remove_from_role(permission_id, role_id)`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Роль или право не найдены|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|

## Method: `set_permissions(server_id: UUID, role_id: UUID, permission_ids: list[UUID], permission_mask: int) -> ServerRole`

### Purpose
Устанавливает полный набор прав для роли, заменяя существующие.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission → `ForbiddenException` если недостаточно прав
2. Получить роль по `role_id` → `NotFoundException` если не найдена
3. Вызвать `permission_repo.bulk_set_for_role(permission_ids, role_id)`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Роль не найдена; один из `permission_ids` ссылается на несуществующее право|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|

## Method: `delete_role(server_id: UUID, role_id: UUID, permission_mask: int) -> None`

### Purpose
Удаляет роль с сервера.

### Algorithm
1. Проверить `EDIT_SERVER_ROLES` permission → `ForbiddenException` если недостаточно прав
2. Получить роль по `role_id` → `NotFoundException` если не найдена
3. Вызвать `role_repo.delete(role_id)` → если результат `False` → `NotFoundException`

### Exceptions
|Exception|Condition|
|---|---|
|`NotFoundException`|Роль не найдена|
|`ForbiddenException`|Недостаточно прав (требуется `EDIT_SERVER_ROLES`)|
