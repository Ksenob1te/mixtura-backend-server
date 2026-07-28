# Member — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/member.py`
- **Service file:** `src/core/services/member.py`, `src/core/services/access_control.py`
- **Commands file:** `src/core/commands/member.py`
- **Results file:** `src/core/results/member.py`
- **Request models:** `src/app/rabbit/models/member.py`

## Response Schemas

The following response types are defined in `src/app/rabbit/models/member.py` and reused across multiple queues in this module.

### MemberResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ID участника |
| `server_id` | `UUID` | ID сервера |
| `user_id` | `UUID \| None` | ID пользователя (`None` для виртуального участника) |
| `nickname` | `str` | Отображаемое имя |
| `joined_at` | `datetime` | Дата присоединения |
| `server_role` | `ServerRoleResponse \| None` | Роль на сервере (см. `src/app/rabbit/models/role.py`) |

### AccessResponse

| Field | Type | Description |
|-------|------|-------------|
| `member` | `MemberResponse \| None` | Данные участника; `None` если не найден на публичном сервере |
| `permission_mask` | `int` | Битовая маска прав |
| `restriction_mask` | `int` | Битовая маска ограничений |

### MemberPermissionResponse

| Field | Type | Description |
|-------|------|-------------|
| `permissions` | `list[PermissionResponse]` | Список прав (см. `src/app/rabbit/models/role.py`) |
| `restrictions` | `list[MemberRestrictionResponse]` | Список ограничений |

### MemberRestrictionResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ID ограничения |
| `reason` | `str` | Причина |
| `expiration_date` | `datetime` | Дата истечения |
| `restriction` | `RestrictionResponse` | Тип ограничения |

### RestrictionResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ID типа ограничения |
| `code` | `str` | Код ограничения |

## Shared Schemas

- `ResponseMessage[T]` — см. [_shared/response-wrapper.md](../../_shared/response-wrapper.md)
- `StatusResponse` — см. [_shared/response-wrapper.md](../../_shared/response-wrapper.md)
- `AccessDataRequest` — см. [_shared/access-data.md](../../_shared/access-data.md)
- `PaginationRequest` — см. [_shared/pagination.md](../../_shared/pagination.md)

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `member.by_user` | `GetMemberByUserRequest` | `AccessResponse` | Получение участника по user\_id |
| `member.list` | `GetMemberListRequest` | `list[MemberResponse]` | Список активных участников сервера |
| `member.join` | `JoinServerRequest` | `MemberResponse` | Присоединение к серверу |
| `member.virtual.create` | `VirtualMemberCreateRequest` | `MemberResponse` | Создание виртуального участника |
| `member.get` | `MemberGetInfoRequest` | `MemberResponse` | Получение участника по ID |
| `member.permissions.get` | `MemberPermissionRequest` | `MemberPermissionResponse` | Права и ограничения текущего участника |
| `member.update` | `MemberUpdateRequest` | `MemberResponse` | Обновление участника |
| `member.kick` | `KickMemberRequest` | `StatusResponse` | Исключение участника |
| `member.virtual.migrate` | `MemberMigrationRequest` | `MemberResponse` | Миграция виртуального участника |
| `server.global.restrictions` | _(нет)_ | `list[RestrictionResponse]` | Глобальные типы ограничений |
| `member.restriction.list` | `GetMemberRestrictionsRequest` | `list[MemberRestrictionResponse]` | Ограничения участника |
| `member.restriction.add` | `AddMemberRestrictionRequest` | `MemberRestrictionResponse` | Наложение ограничения |
| `member.restriction.remove` | `RemoveMemberRestrictionRequest` | `StatusResponse` | Снятие ограничения |

---

## Queue: `member.by_user`

### Command: `GetMemberByUserRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | `UUID` | Yes | |
| `user_id` | `UUID` | Yes | |

### Result: `AccessResponse`

См. [AccessResponse](#accessresponse)

### Behavior
- Если участник не найден, а сервер публичный — возвращается `AccessResponse` с `member = None` и нулевыми масками.
- Если участник не найден, а сервер приватный — `NotFoundException`.
- При найденном участнике вычисляются маска прав через роль участника и маска ограничений.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден; сервер приватный и участник не найден |

---

## Queue: `member.list`

### Command: `GetMemberListRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `pagination` | `PaginationRequest` | Yes | Пагинация |
| `nickname_filter` | `str` | No | Фильтр по нику (по умолчанию `""`) |

### Result: `list[MemberResponse]`

Возвращает список только активных участников сервера.

---

## Queue: `member.join`

### Command: `JoinServerRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | `UUID` | Yes | |
| `user_id` | `UUID` | Yes | |
| `nickname` | `str` | Yes | |
| `restriction_mask` | `int` | Yes | Маска ограничений |

### Result: `MemberResponse`

См. [MemberResponse](#memberresponse)

### Behavior
- Проверяется существование и публичный статус сервера (`server.public`).
- Если у пользователя установлен `SERVER_BAN` в `restriction_mask` — сервер считается ненайденным (`NotFoundException`).
- Если участник уже существует и активен — возвращается существующий.
- Если участник уже существует, но неактивен — производится реактивация.
- Новый участник создаётся с `server_role_id = None`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден или не публичный; установлен `SERVER_BAN`; внешний ключ сервера не найден |
| `InternalLogicException` | Ошибка целостности при создании |

---

## Queue: `member.virtual.create`

### Command: `VirtualMemberCreateRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `nickname` | `str` | Yes | |

### Result: `MemberResponse`

См. [MemberResponse](#memberresponse)

### Behavior
- Проверяется право `CREATE_VIRTUAL` в маске прав `access_data.permission_mask`.
- Виртуальный участник создаётся с `user_id = None`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Нет права `CREATE_VIRTUAL` |
| `NotFoundException` | Внешний ключ сервера не найден |
| `InternalLogicException` | Ошибка целостности при создании |

---

## Queue: `member.get`

### Command: `MemberGetInfoRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID запрашиваемого участника |

### Result: `MemberResponse`

См. [MemberResponse](#memberresponse)

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник с указанным ID не найден |

---

## Queue: `member.permissions.get`

### Command: `MemberPermissionRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |

### Result: `MemberPermissionResponse`

См. [MemberPermissionResponse](#memberpermissionresponse)

### Behavior
- `access_data.member_id` используется как идентификатор запрашиваемого участника.
- Права вычисляются на основе роли участника с учётом права `ADMINISTRATOR` и владельца сервера.
- Если `access_data.member_id` равен `None` — `NotFoundException`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | `member_id` равен `None` |

---

## Queue: `member.update`

### Command: `MemberUpdateRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID изменяемого участника |
| `name` | `str \| None` | No | Новое отображаемое имя |
| `server_role_id` | `UUID \| None` | No | Новая роль |

### Result: `MemberResponse`

См. [MemberResponse](#memberresponse)

### Behavior
- Если `access_data.member_id` равен `None` — `NotFoundException`.
- Если изменяемый участник не найден или не принадлежит тому же серверу — `NotFoundException`.
- **Смена имени:**
  - Если участник меняет себе имя — проверяется отсутствие ограничения `SELF_EDIT_NAME`.
  - Если имя меняет другой участник — проверяется право `EDIT_NAME`.
- **Смена роли:**
  - Проверяется право `EDIT_ROLES`.
  - Назначаемая роль должна существовать и принадлежать тому же серверу.
  - Проверяется иерархия ролей: `issuer_field.server_role.position > assign_role.position`.
  - Владелец сервера может назначать любую роль.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Member ID is `None`; целевой участник не найден; роль не найдена; издатель не найден |
| `ForbiddenException` | Нет права на смену имени/роли; ограничение `SELF_EDIT_NAME`; недостаточная позиция роли |
| `InternalLogicException` | Сервер участника-издателя не найден |

---

## Queue: `member.kick`

### Command: `KickMemberRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID исключаемого участника |

### Result: `StatusResponse`

См. [_shared/response-wrapper.md](../../_shared/response-wrapper.md)

### Behavior
- Проверяется право `KICK_MEMBERS`; издатель не может исключить сам себя.
- Целевой участник и издатель должны существовать и принадлежать одному серверу.
- Иерархия ролей: нельзя исключить владельца сервера (`server_field.owner_id`) или участника с ролью выше/равной роли издателя.
- При успехе участник деактивируется (`active = false`).

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник не найден (любой из пары); member ID is `None` |
| `ForbiddenException` | Нет права `KICK_MEMBERS`; попытка исключить себя; недостаточная позиция роли; попытка исключить владельца |

---

## Queue: `member.virtual.migrate`

### Command: `MemberMigrationRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `origin_member_id` | `UUID` | Yes | Исходный виртуальный участник |
| `target_member_id` | `UUID` | Yes | Целевой участник |

### Result: `MemberResponse`

См. [MemberResponse](#memberresponse)

### Behavior
- Проверяется право `MIGRATE_MEMBERS`.
- Оба участника должны существовать и принадлежать одному серверу.
- Исходный участник должен иметь `user_id` (то есть не быть виртуальным).
- У целевого участника `user_id` должен быть `None` (виртуальный).
- Процесс: у исходного участника очищается `user_id` и он деактивируется; `user_id` переносится в целевого участника.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Нет права `MIGRATE_MEMBERS` |
| `NotFoundException` | Любой из участников не найден или не принадлежит серверу |
| `MigrationException` | Исходный участник не имеет `user_id`; целевой участник уже имеет `user_id` |

---

## Queue: `server.global.restrictions`

### Command: Пустая команда (без полей).

### Result: `list[RestrictionResponse]`

См. [RestrictionResponse](#restrictionresponse)

---

## Queue: `member.restriction.list`

### Command: `GetMemberRestrictionsRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID участника |

### Result: `list[MemberRestrictionResponse]`

См. [MemberRestrictionResponse](#memberrestrictionresponse)

### Behavior
- Получает целевого участника; извлекает его `user_id` и запрашивает ограничения для этого `user_id` на сервере.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Целевой участник не найден |

---

## Queue: `member.restriction.add`

### Command: `AddMemberRestrictionRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID участника для ограничения |
| `restriction_id` | `UUID` | Yes | ID типа ограничения |
| `reason` | `str` | Yes | Причина |
| `expiration_date` | `datetime` | Yes | Дата истечения |

### Result: `MemberRestrictionResponse`

См. [MemberRestrictionResponse](#memberrestrictionresponse)

### Behavior
- Проверяется наличие права на наложение данного типа ограничения: `PERMISSION.check_permission(permission_mask, f"restrict_{restriction.code}")`.
- Целевой участник и тип ограничения должны существовать.
- Проверяется иерархия ролей (`_can_manipulate_restrictions`): издатель должен иметь роль выше целевого; владелец сервера может накладывать ограничения на любого, кроме себя.
- Нельзя наложить ограничение на владельца сервера.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Member ID is `None`; целевой участник не найден; тип ограничения не найден |
| `ForbiddenException` | Нет права `restrict_{code}`; недостаточная позиция роли; попытка ограничить владельца |
| `InternalLogicException` | Издатель или его сервер не найдены |

---

## Queue: `member.restriction.remove`

### Command: `RemoveMemberRestrictionRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `target_member_id` | `UUID` | Yes | ID участника |
| `member_restriction_id` | `UUID` | Yes | ID ограничения для снятия |

### Result: `StatusResponse`

См. [_shared/response-wrapper.md](../../_shared/response-wrapper.md)

### Behavior
- Проверяется наличие права на снятие данного типа ограничения: `PERMISSION.check_permission(permission_mask, f"restrict_{restriction.code}")`.
- Ограничение должно принадлежать указанному участнику.
- Проверяется иерархия ролей (`_can_manipulate_restrictions`): издатель должен иметь роль выше целевого.
- Ограничение физически удаляется.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Member ID is `None`; издатель не найден; ограничение не найдено или не принадлежит участнику |
| `ForbiddenException` | Нет права `restrict_{code}`; недостаточная позиция роли |
| `InternalLogicException` | Участник ограничения не найден; сервер издателя не найден |
