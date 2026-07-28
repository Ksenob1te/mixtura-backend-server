# CoreService — Business Logic

## Overview

- **File:** `src/core/services/core.py`
- **Private helpers:**
  - `_copy_role_set(global_role_set, server_id) -> GameRoleSet` — копирует глобальный набор ролей на сервер и создаёт роль «Leader» с ограничением 1 участник
  - `_copy_rating_set(global_rating_set, server_id) -> RatingSet` — копирует глобальный набор рейтингов на сервер

## Dependencies

### Repositories

| Repository | Purpose |
|------------|---------|
| `ServerRepositoryProtocol` | CRUD серверов, фильтрация публичных серверов и серверов участника |
| `GameRepositoryProtocol` | Получение списка глобальных игр |
| `GameRoleSetRepositoryProtocol` | Получение глобальных наборов ролей, копирование на сервер |
| `GameRoleRepositoryProtocol` | Создание роли «Leader» при копировании набора ролей |
| `RatingSetRepositoryProtocol` | Получение глобальных наборов рейтингов, копирование на сервер |
| `RatingRepositoryProtocol` | Копирование рейтингов |
| `PermissionRepositoryProtocol` | Список всех прав доступа |
| `RestrictionRepositoryProtocol` | Список всех типов ограничений |
| `MemberRepositoryProtocol` | Создание первого участника (владельца) при создании сервера |

---

## Method: `get_global_role_templates() -> list[GameRoleSet]`

### Purpose
Возвращает список всех глобальных шаблонов наборов ролей.

### Algorithm
1. Вызвать `game_role_set_repo.get_global()`

---

## Method: `get_global_rating_templates() -> list[RatingSet]`

### Purpose
Возвращает список всех глобальных шаблонов наборов рейтингов.

### Algorithm
1. Вызвать `rating_set_repo.get_global()`

---

## Method: `get_global_permissions() -> list[Permission]`

### Purpose
Возвращает список всех прав доступа в системе.

### Algorithm
1. Вызвать `permission_repo.list_all()`

---

## Method: `get_global_restrictions() -> list[Restriction]`

### Purpose
Возвращает список всех типов ограничений в системе.

### Algorithm
1. Вызвать `restriction_repo.list_all()`

---

## Method: `get_global_games() -> list[Game]`

### Purpose
Возвращает список всех глобальных игр.

### Algorithm
1. Вызвать `game_repo.get_all()`

---

## Method: `list_servers(page: int | None, name_filter: str | None, page_size: int = 50) -> list[Server]`

### Purpose
Возвращает список публичных серверов с пагинацией и фильтром по имени.

### Algorithm
1. Вызвать `server_repo.list_public(page, name_filter, page_size)`

---

## Method: `list_user_servers(user_id: UUID, page: int | None, name_filter: str | None, page_size: int = 50) -> list[Server]`

### Purpose
Возвращает список серверов, где пользователь является участником.

### Algorithm
1. Вызвать `server_repo.list_by_user(user_id, page, name_filter, page_size)`

---

## Method: `create_server(name, owner_id, username, description, public, rating_set_id, role_set_id) -> Server`

### Purpose
Создаёт новый сервер: валидирует глобальные шаблоны, копирует их на сервер и создаёт первого участника-владельца.

### Algorithm
1. Проверить `role_set_id` и `rating_set_id` на `None` → `NotFoundException`
2. Получить глобальный набор ролей через `game_role_set_repo.get(role_set_id)` → если не найден или `is_global == False` → `NotFoundException`
3. Получить глобальный набор рейтингов через `rating_set_repo.get(rating_set_id)` → если не найден или `is_global == False` → `NotFoundException`
4. Вызвать `server_repo.create(name, owner_id, public, description)`
   - `IntegrityForeignException` → `NotFoundException`
   - `IntegrityUniqueException` / `IntegrityUnknownException` → `InternalLogicException`
5. Копировать набор рейтингов на сервер через `_copy_rating_set()`
6. Копировать набор ролей на сервер через `_copy_role_set()` (создаёт роль «Leader»)
7. Установить `server.rating_set` и `server.role_set`
8. Создать первого участника (владельца) через `member_repo.create(server_id, owner_id, username, server_role_id=None)`
   - `IntegrityForeignException` → `NotFoundException`
   - `IntegrityUniqueException` / `IntegrityUnknownException` → `InternalLogicException`
9. Вернуть сервер

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Не передан `role_set_id` или `rating_set_id` |
| `NotFoundException` | Глобальный набор ролей не найден или не является глобальным |
| `NotFoundException` | Глобальный набор рейтингов не найден или не является глобальным |
| `NotFoundException` | Ошибка внешнего ключа при создании сервера или участника |
| `InternalLogicException` | Ошибка целостности (Unique, Unknown) при создании сервера или участника |

---

## Method: `get_server(server_id: UUID) -> Server`

### Purpose
Возвращает сервер по ID.

### Algorithm
1. Вызвать `server_repo.get(server_id)`
2. Если результат `None` → `NotFoundException`

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Method: `update_server(server_id, name, description, public, banner_id, icon_id, permission_mask) -> Server`

### Purpose
Обновляет указанные поля сервера с индивидуальной проверкой прав на каждое изменяемое поле.

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → если `None` → `NotFoundException`
2. Для каждого переданного поля, значение которого отличается от текущего:
   - Проверить соответствующее разрешение (`EDIT_SERVER_NAME`, `EDIT_SERVER_DESCRIPTION`, `EDIT_SERVER_PUBLIC`, `EDIT_SERVER_ICON`, `EDIT_SERVER_BANNER`) → `ForbiddenException`
   - Вызвать `server_repo.set_<field>(server, value)`
3. Вернуть обновлённый сервер

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав для изменения конкретного поля |

---

## Method: `delete_server(server_id: UUID, permission_mask: int = 0) -> None`

### Purpose
Удаляет сервер с проверкой права `DELETE_SERVER`.

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → если `None` → `NotFoundException`
2. Проверить `DELETE_SERVER` permission → `ForbiddenException`
3. Вызвать `server_repo.delete(server_id)` → если `False` → `InternalLogicException`

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |
| `InternalLogicException` | Ошибка при удалении сервера |

---

## Method: `delete_server_banner(server_id: UUID, permission_mask: int = 0) -> Server`

### Purpose
Удаляет баннер сервера (устанавливает `banner_id = None`).

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → если `None` → `NotFoundException`
2. Проверить `EDIT_SERVER_BANNER` permission → `ForbiddenException`
3. Вызвать `server_repo.set_banner(server, None)`

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |

---

## Method: `delete_server_icon(server_id: UUID, permission_mask: int = 0) -> Server`

### Purpose
Удаляет иконку сервера (устанавливает `icon_id = None`).

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → если `None` → `NotFoundException`
2. Проверить `EDIT_SERVER_ICON` permission → `ForbiddenException`
3. Вызвать `server_repo.set_icon(server, None)`

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |
