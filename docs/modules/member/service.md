# MemberService — Business Logic

## Overview
- **File:** `src/core/services/member.py`
- **Private helper:** `_can_manipulate_roles(issuer_field: Member, assign_role: ServerRole, server_field: Server) -> None` — проверяет, может ли выдающий участник назначать конкретную роль: роль выдающего должна быть строго выше назначаемой, либо выдающий является владельцем сервера

## Dependencies

### Repositories
- `MemberRepositoryProtocol` — CRUD участников, управление статусом и ролями
- `ServerRepositoryProtocol` — получение сервера для проверки существования и публичности
- `ServerRoleRepositoryProtocol` — получение ролей для проверки иерархии

## Method: `list_members(server_id: UUID, page: int | None, nickname_filter: str, page_size: int) -> list[Member]`

### Purpose
Возвращает список активных участников сервера с пагинацией и фильтрацией по нику.

### Algorithm
1. Вызвать `member_repo.list_active_for_server(server_id, page, nickname_filter, page_size)`

## Method: `join_server(server_id: UUID, user_id: UUID, nickname: str, restriction_mask: int) -> Member`

### Purpose
Присоединяет пользователя к публичному серверу в качестве участника.

### Algorithm
1. Получить сервер через `server_repo.get()` → `NotFoundException` если сервер не найден или не публичный
2. Проверить ограничение `SERVER_BAN` в restriction_mask → `NotFoundException` (скрыто)
3. Проверить существующего участника через `member_repo.get_by_user_in_server()`
4. Если участник существует и неактивен: активировать через `member_repo.activate()`
5. Если участник существует и активен: вернуть существующего
6. Если не существует: создать через `member_repo.create()` с `server_role_id=None`
   → `IntegrityForeignException` → `NotFoundException`
   → `IntegrityUnknownException` / `IntegrityUniqueException` → `InternalLogicException`
7. Вернуть участника

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден, не публичный, или пользователь забанен |
| `InternalLogicException` | Ошибка целостности при создании (дубликат, неизвестная ошибка) |

## Method: `create_virtual(server_id: UUID, nickname: str, permission_mask: int) -> Member`

### Purpose
Создаёт виртуального участника (без привязки к пользователю).

### Algorithm
1. Проверить `CREATE_VIRTUAL` permission → `ForbiddenException`
2. Создать через `member_repo.create(server_id, user_id=None, nickname, server_role_id=None)`
   → `IntegrityForeignException` → `NotFoundException`
   → `IntegrityUnknownException` → `InternalLogicException`
3. Вернуть участника

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден (FK constraint) |
| `ForbiddenException` | Недостаточно прав |
| `InternalLogicException` | Неизвестная ошибка целостности |

## Method: `get_member(member_id: UUID) -> Member`

### Purpose
Возвращает участника по ID.

### Algorithm
1. Вызвать `member_repo.get(member_id)`
2. Если `None` → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник не найден |

## Method: `update_member(server_id: UUID, issuer_id: UUID, permission_mask: int, restriction_mask: int, member_id: UUID, name: str | None, server_role_id: UUID | None) -> Member`

### Purpose
Обновляет ник и/или роль участника с проверкой прав.

### Algorithm
1. Получить изменяемого участника через `member_repo.get()` → `NotFoundException` если не найден или `server_id` не совпадает
2. Если `name` указан и отличается от текущего:
   - Если issuer == target: проверить `SELF_EDIT_NAME` restriction → `ForbiddenException`
   - Если issuer != target: проверить `EDIT_NAME` permission → `ForbiddenException`
   - Применить через `member_repo.set_nickname()`
3. Если `server_role_id` указан:
   - Проверить `EDIT_ROLES` permission → `ForbiddenException`
   - Получить назначаемую роль через `server_role_repo.get()` → `NotFoundException` если не найдена или не с этого сервера
   - Получить issuer через `member_repo.get()` → `NotFoundException`
   - Получить сервер через `issuer.server` → `InternalLogicException`
   - Вызвать `_can_manipulate_roles()` → `ForbiddenException`
   - Применить через `member_repo.set_role()`
4. Вернуть участника

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник не найден, не на указанном сервере, или роль не найдена |
| `ForbiddenException` | Недостаточно прав для изменения ника или роли, нарушение иерархии ролей |
| `InternalLogicException` | Сервер issuer не найден |

## Method: `kick_member(issuer_id: UUID, server_id: UUID, member_id: UUID, permission_mask: int) -> None`

### Purpose
Исключает участника с сервера (деактивирует).

### Algorithm
1. Проверить `KICK_MEMBERS` permission или `issuer_id == member_id` → `ForbiddenException`
2. Получить исключаемого участника и выдающего через `member_repo.get()` → `NotFoundException` если кто-то не найден или сервера не совпадают
3. Получить сервер выдающего через `issuer.server` → `InternalLogicException` если не найден
4. Проверить, что target не является владельцем сервера (`server.owner_id == target.user_id`) → `ForbiddenException`
5. Проверить иерархию ролей: роль target не выше и не равна роли issuer → `ForbiddenException`
6. Деактивировать участника через `member_repo.deactivate()`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник (исключаемый или выдающий) не найден или на другом сервере |
| `ForbiddenException` | Недостаточно прав, попытка исключить себя, владельца, или участника с равной/высшей ролью |
| `InternalLogicException` | Сервер выдающего не найден |

## Method: `migrate_member(server_id: UUID, origin_member_id: UUID, target_member_id: UUID, permission_mask: int) -> Member`

### Purpose
Переносит привязку реального пользователя от одного участника к другому: `origin` теряет пользователя (становится виртуальным и деактивируется), `target` получает пользователя.

### Algorithm
1. Проверить `MIGRATE_MEMBERS` permission → `ForbiddenException`
2. Получить исходного и целевого участников через `member_repo.get()`
3. Проверить, что оба существуют и находятся на указанном сервере → `NotFoundException`
4. Проверить, что `origin.user_id` не `None` (origin — реальный пользователь) → `MigrationException`
5. Удалить `user_id` у origin через `member_repo.remove_user(origin)`
6. Деактивировать origin через `member_repo.deactivate(origin)`
7. Перенести `user_id` в target через `member_repo.set_user_if_none(target, user_id)`
8. Если `set_user_if_none` вернул `False` (target уже имеет пользователя) → `MigrationException`
9. Вернуть target

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав |
| `NotFoundException` | Один из участников не найден или не на указанном сервере |
| `MigrationException` | Origin не имеет пользователя, или target уже имеет пользователя |
