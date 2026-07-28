# InviteService — Business Logic

## Overview
- **File:** `src/core/services/invite.py`
- **Private helpers:** нет

Обрабатывает жизненный цикл приглашений на сервер: получение информации по ключу, использование для вступления, создание, отзыв и список.

## Dependencies

### Repositories
| Repository | Protocol | Implementation | Назначение |
|------------|----------|----------------|------------|
| `InviteRepositoryProtocol` | `src/core/interfaces/repo/invite.py` | `InviteRepository` | CRUD приглашений, поиск по ключу, декремент лимита |
| `ServerRepositoryProtocol` | `src/core/interfaces/repo/server.py` | `ServerRepository` | Проверка существования сервера |
| `MemberRepositoryProtocol` | `src/core/interfaces/repo/member.py` | `MemberRepository` | Получение/создание/активация участника |

### Config
- `RESTRICTION` — проверка `SERVER_BAN` при использовании приглашения
- `PERMISSION` — проверка `EDIT_INVITES` для управления приглашениями

---

## Method: `get_invite_info(key) -> Invite`

### Purpose
Возвращает ORM-модель приглашения по его ключу.

### Algorithm
1. Вызвать `invite_repo.get_by_key(key)`
2. Если результат `None` → `NotFoundException("Invite not found")`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение с указанным ключом не найдено |

---

## Method: `use_invite(key, user_id, nickname, restriction_mask) -> Member`

### Purpose
Активирует приглашение: присоединяет пользователя к серверу (или активирует существующего неактивного участника).

### Algorithm
1. Вызвать `invite_repo.get_by_key(key)`
2. Если приглашение не найдено или `invite.use_limit <= 0` → `NotFoundException("Invite not found")`
3. Проверить `RESTRICTION.check_restriction(restriction_mask, RESTRICTION.SERVER_BAN)` — если установлен → `NotFoundException("Invite not found")` (скрыто, чтобы не раскрывать факт бана)
4. Получить сервер через навигационное свойство `invite_field.server`
5. Вызвать `member_repo.get_by_user_in_server(server_id, user_id)`:
   - Если участник существует и `active == False`: вызвать `member_repo.activate(existing_member)`, использовать существующего
   - Если участник существует и `active == True`: использовать существующего (не меняя лимит)
   - Если не существует: создать через `member_repo.create(server_id, user_id, nickname, server_role_id=None)`
     - `IntegrityForeignException` → `NotFoundException`
     - `IntegrityUnknownException` → `InternalLogicException`
6. После создания нового участника: `invite_repo.decrement_use_limit(invite_field)`
7. Вернуть `member_field`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение не найдено, лимит использований исчерпан, пользователь забанен, или ошибка внешнего ключа при создании участника |
| `InternalLogicException` | Неизвестная ошибка целостности БД при создании участника |

---

## Method: `list_invites(server_id, permission_mask) -> list[Invite]`

### Purpose
Возвращает список всех приглашений указанного сервера.

### Algorithm
1. Вызвать `server_repo.get(server_id)`
2. Если сервер не найден → `NotFoundException("Server not found")`
3. Проверить `PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES)`
   - Если нет прав → `ForbiddenException("Unable to list invites")`
4. Вызвать `invite_repo.list_for_server(server_id)`
5. Вернуть результат, приведённый к `list[Invite]`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |

---

## Method: `create_invite(server_id, use_limit, inviter_id, permission_mask) -> Invite`

### Purpose
Создаёт новое приглашение на сервер.

### Algorithm
1. Проверить `PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES)`
   - Если нет прав → `ForbiddenException("Unable to create invite")`
2. Нормализовать `use_limit`:
   - Если `None` → `0` (без лимита)
   - Если `< 0` → `0`
3. Вызвать `invite_repo.create(server_id, use_limit, inviter_id)`
4. Обработать исключения репозитория:
   - `IntegrityForeignException` → `NotFoundException` (сервер или пригласивший не найден)
   - `IntegrityUniqueException` / `IntegrityUnknownException` / `InviteUniqueException` → `InternalLogicException`
5. Вернуть созданную модель `Invite`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |
| `NotFoundException` | Сервер или пригласивший участник не найден (ошибка внешнего ключа) |
| `InternalLogicException` | Ошибка создания записи в БД (нарушение уникальности или прочее) |

---

## Method: `revoke_invite(server_id, invite_id, permission_mask) -> None`

### Purpose
Отзывает приглашение: удаляет запись из БД.

### Algorithm
1. Вызвать `invite_repo.get(invite_id)`
2. Если приглашение не найдено или `invite.server_id != server_id` → `NotFoundException("Invite not found")`
3. Проверить `PERMISSION.check_permission(permission_mask, PERMISSION.EDIT_INVITES)`
   - Если нет прав → `ForbiddenException("Unable to revoke invite")`
4. Вызвать `invite_repo.delete(invite_id)`
5. Если `delete` вернул `False` → `NotFoundException("Invite not found")`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение не найдено или не принадлежит указанному серверу |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |
