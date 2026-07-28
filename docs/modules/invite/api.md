# Invite — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/invite.py`
- **Service file:** `src/core/services/invite.py`
- **Commands file:** `src/core/commands/invite.py`
- **Request models:** `src/app/rabbit/models/invite.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `invite.get_by_key` | `GetInviteByKeyRequest` | `InviteKeyResponse` | Информация по ключу приглашения |
| `invite.get_restriction` | `GetUserRestrictionRequest` | `int` | Маска ограничений пользователя |
| `invite.use` | `UseInviteRequest` | `MemberResponse` | Использование приглашения для вступления на сервер |
| `invite.list` | `GetInviteListRequest` | `list[InviteAdminResponse]` | Список приглашений сервера |
| `invite.create` | `InviteCreateRequest` | `InviteAdminResponse` | Создание приглашения |
| `invite.revoke` | `RevokeInviteRequest` | `StatusResponse` | Отзыв приглашения |

---

## Queue: `invite.get_by_key`

### Command: `GetInviteByKeyRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `str` | Yes | Ключ приглашения |

### Result: `InviteKeyResponse`
| Field | Type | Description |
|-------|------|-------------|
| `inviter` | `ReducedMemberResponse` | Участник, создавший приглашение |
| `server` | `ServerListResponse` | Информация о сервере |

**`ReducedMemberResponse`:**
| Field | Type |
|-------|------|
| `id` | `UUID` |
| `nickname` | `str` |
| `user_id` | `UUID \| None` |

**`ServerListResponse`:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `description` | `str` | |
| `icon_id` | `UUID \| None` | |
| `banner_id` | `UUID \| None` | |
| `owner_id` | `UUID` | |
| `public` | `bool` | |
| `created_at` | `datetime` | |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение с указанным ключом не найдено |

---

## Queue: `invite.get_restriction`

### Command: `GetUserRestrictionRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `UUID` | Yes | ID пользователя |
| `server_id` | `UUID` | Yes | ID сервера |

### Result: `int`
Битовая маска ограничений пользователя на сервере.

---

## Queue: `invite.use`

### Command: `UseInviteRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `UUID` | Yes | ID пользователя |
| `restriction_mask` | `int` | Yes | Маска ограничений пользователя |
| `nickname` | `str` | Yes | Никнейм на сервере |
| `key` | `str` | Yes | Ключ приглашения |

### Result: `MemberResponse`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `nickname` | `str` | |
| `user_id` | `UUID \| None` | |
| `server_id` | `UUID` | |
| `joined_at` | `datetime` | |
| `server_role` | `ServerRoleResponse \| None` | |

### Behavior
- Проверяет существование приглашения и лимит использований (`use_limit > 0`).
- Проверяет `restriction_mask` на наличие `SERVER_BAN` — если установлен, приглашение считается недействительным.
- Если участник уже существует:
  - Неактивного участника — активирует.
  - Активного — переиспользует существующего.
- Если участник не существует — создаёт нового участника на сервере.
- Уменьшает лимит использований приглашения только при создании нового участника.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение не найдено; лимит использований исчерпан; пользователь забанен на сервере; ошибка внешнего ключа при создании участника |
| `InternalLogicException` | Неизвестная ошибка целостности БД при создании участника |

---

## Queue: `invite.list`

### Command: `GetInviteListRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |

### Result: `list[InviteAdminResponse]`
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ID приглашения |
| `key` | `str` | Ключ приглашения |
| `inviter` | `MemberResponse` | Пригласивший участник |
| `use_limit` | `int` | Оставшийся лимит использований |

**`MemberResponse`:**
| Field | Type |
|-------|------|
| `id` | `UUID` |
| `nickname` | `str` |
| `user_id` | `UUID \| None` |
| `server_id` | `UUID` |
| `joined_at` | `datetime` |
| `server_role` | `ServerRoleResponse \| None` |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |

---

## Queue: `invite.create`

### Command: `InviteCreateRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `use_limit` | `int \| None` | No | Лимит использований (по умолчанию 0 — неограниченно) |

### Result: `InviteAdminResponse`
Поля — см. [Queue: `invite.list`](#queue-invitelist).

### Behavior
- Если `use_limit` не указан или отрицательный — устанавливается в 0 (без лимита).
- Генерирует уникальный ключ для приглашения.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |
| `NotFoundException` | Сервер не найден (ошибка внешнего ключа) |
| `InternalLogicException` | Ошибка создания записи в БД (нарушение уникальности или прочее) |

---

## Queue: `invite.revoke`

### Command: `RevokeInviteRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `invite_id` | `UUID` | Yes | ID приглашения |

### Result: `StatusResponse`
| Field | Type | Description |
|-------|------|-------------|
| `status` | `str` | Всегда `"ok"` |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Приглашение не найдено или не принадлежит указанному серверу |
| `ForbiddenException` | Недостаточно прав (требуется `EDIT_INVITES`) |
