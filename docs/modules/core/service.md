# CoreService — Business Logic

## Overview

- **File:** `src/core/services/core.py`

## Dependencies

### Repositories

| Repository | Purpose |
|------------|---------|
| `ServerRepositoryProtocol` | CRUD серверов, фильтрация публичных серверов и серверов участника |
| `PermissionRepositoryProtocol` | Список всех прав доступа |
| `RestrictionRepositoryProtocol` | Список всех типов ограничений |
| `MemberRepositoryProtocol` | Создание первого участника (владельца) при создании сервера |

> Игры и их наборы ролей/рейтингов больше не создаются и не читаются через `CoreService` — управление играми и глобальными шаблонами перенесено в `GameService` ([modules/game/service.md](../game/service.md)).

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

## Method: `create_server(name, owner_id, username, description, public) -> Server`

### Purpose
Создаёт новый сервер и первого участника-владельца. Больше не принимает и не копирует какие-либо шаблоны ролей/рейтингов — они принадлежат играм, а не серверу.

### Algorithm
1. `server_repo.create(ServerCreate(name=name, owner_id=owner_id, public=public, description=description))`
   - `IntegrityForeignException` → `NotFoundException`
   - `IntegrityUniqueException` / `IntegrityUnknownException` → `InternalLogicException`
2. Создать первого участника (владельца) через `member_repo.create(MemberCreate(server_id=server.id, user_id=owner_id, nickname=username))`
   - `IntegrityForeignException` → `NotFoundException`
   - `IntegrityUniqueException` / `IntegrityUnknownException` → `InternalLogicException`
3. Вернуть сервер

### Exceptions

| Exception | Condition |
|-----------|-----------|
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
   - Добавить поле в `update_data`
3. Если `update_data` не пуст — вызвать `server_repo.update(ServerUpdate(id=server_id, **update_data))`
4. Вернуть сервер

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

### Behavior
- Каскадно удаляет `owned_games` сервера (локальные игры) и их `role_set`/`rating_set`/роли/рейтинги. Глобальные игры не затрагиваются.

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
3. Вызвать `server_repo.update(ServerUpdate(id=server_id, banner_id=None))`

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
3. Вызвать `server_repo.update(ServerUpdate(id=server_id, icon_id=None))`

### Exceptions

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |
