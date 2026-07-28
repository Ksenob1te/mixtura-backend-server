# Game Role — Queue Contracts

## Overview

- **Handler file:** `src/app/rabbit/api/game_role.py`
- **Service file:** `src/core/services/game_role.py`
- **Commands file:** `src/core/commands/game_role.py`
- **Request/Response models:** `src/app/rabbit/models/game_role.py`

Обработчики используют `ResponseMessage[T]` в качестве конверта ответа (см. [Response Envelope](../../_shared/response-wrapper.md)). Очереди `role_set.*` защищены `AccessDataRequest` (см. [Access Data](../../_shared/access-data.md)) и требуют право `EDIT_ROLE_SET`, применимое к набору ролей **локальной** игры сервера. Очереди `role_set.global.*` не принимают `access_data` и не проверяют права — авторизация обеспечивается gateway (только сайт-админ может публиковать в `*.global.*` очереди); они действуют на набор ролей **глобальной** игры.

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `role_set.update` | `GameRoleSetUpdateRequest` | `GameRoleSetResponse` | Обновление набора ролей локальной игры |
| `role_set.role.create` | `GameRoleItemCreateRequest` | `GameRoleItemResponse` | Создание роли в наборе локальной игры |
| `role_set.role.update` | `GameRoleItemUpdateRequest` | `GameRoleItemResponse` | Обновление роли локальной игры |
| `role_set.role.icon.delete` | `GameRoleItemDeleteRequest` | `StatusResponse` | Удаление иконки роли локальной игры |
| `role_set.role.delete` | `GameRoleItemDeleteRequest` | `StatusResponse` | Удаление роли локальной игры |
| `role_set.global.update` | `GlobalGameRoleSetUpdateRequest` | `GameRoleSetResponse` | Обновление набора ролей глобальной игры |
| `role_set.global.role.create` | `GlobalGameRoleCreateRequest` | `GameRoleItemResponse` | Создание роли в наборе глобальной игры |
| `role_set.global.role.update` | `GlobalGameRoleUpdateRequest` | `GameRoleItemResponse` | Обновление роли глобальной игры |
| `role_set.global.role.icon.delete` | `GlobalGameRoleDeleteRequest` | `StatusResponse` | Удаление иконки роли глобальной игры |
| `role_set.global.role.delete` | `GlobalGameRoleDeleteRequest` | `StatusResponse` | Удаление роли глобальной игры |

## Общие исключения

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Набор ролей или роль не найдены (глобально либо для указанного сервера) |
| `ForbiddenException` | Локальные очереди: недостаточно прав (`EDIT_ROLE_SET`) либо `role_set_id`/`role_id` указывает на набор глобальной игры. Глобальные очереди: `role_set_id`/`role_id` указывает на набор локальной игры |

> Отдельной очереди для чтения набора ролей больше нет — набор всегда доставляется вложенным внутри `GameDetailResponse` (см. [game/api.md](../game/api.md)).

---

## Queue: `role_set.update`

Обрабатывается `GameRoleService.update_role_set()`. Обновляет название набора ролей локальной игры сервера.

### Command: `GameRoleSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str \| None` | No | Новое название (максимум 32 символа) |

### Result: `GameRoleSetResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `game_id` | `UUID` | ID игры-владельца набора |
| `game_roles` | `list[GameRoleItemResponse]` | Список ролей в наборе |

### Behavior
1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка, что `role_set_id` принадлежит набору ролей локальной игры указанного сервера.
3. Если `name` передан и отличается от текущего — обновление.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу |
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |

---

## Queue: `role_set.global.update`

Обрабатывается `GameRoleService.update_global_role_set()`. Обновляет название набора ролей глобальной игры. Не требует `access_data`.

### Command: `GlobalGameRoleSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str \| None` | No | Новое название (максимум 32 символа) |

### Result: `GameRoleSetResponse`
→ См. таблицу в контракте `role_set.update`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Набор не найден |
| `ForbiddenException` | Набор принадлежит локальной игре |

---

## Queue: `role_set.role.create`

Обрабатывается `GameRoleService.create_role()`. Создаёт новую игровую роль в наборе локальной игры.

### Command: `GameRoleItemCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str` | Yes | Название роли (максимум 32 символа) |
| `min_in_team` | `int` | Yes | Минимальное количество в команде |
| `max_in_team` | `int` | Yes | Максимальное количество в команде |
| `hidden` | `bool` | No | Скрытая роль (по умолчанию `False`) |
| `icon_id` | `UUID \| None` | No | |

### Result: `GameRoleItemResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `icon_id` | `UUID \| None` | |
| `min_in_team` | `int` | |
| `max_in_team` | `int` | |
| `hidden` | `bool` | |

### Behavior
1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка, что `role_set_id` принадлежит набору ролей локальной игры сервера.
3. Создание роли через `role_repo.create()`. При `IntegrityForeignException` → `NotFoundException`; при `IntegrityUnknownException` → `InternalLogicException`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу; FK-ограничение |
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Queue: `role_set.global.role.create`

Обрабатывается `GameRoleService.create_global_role()`. Не требует `access_data`.

### Command: `GlobalGameRoleCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str` | Yes | Максимум 32 символа |
| `min_in_team` | `int` | Yes | |
| `max_in_team` | `int` | Yes | |
| `hidden` | `bool` | No | По умолчанию `False` |
| `icon_id` | `UUID \| None` | No | |

### Result: `GameRoleItemResponse`
→ См. таблицу в контракте `role_set.role.create`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Набор не найден; FK-ограничение |
| `ForbiddenException` | Набор принадлежит локальной игре |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Queue: `role_set.role.update`

Обрабатывается `GameRoleService.update_role()`. Обновляет поля игровой роли локальной игры. Обновляются только переданные поля.

### Command: `GameRoleItemUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `role_id` | `UUID` | Yes | |
| `name` | `str \| None` | No | Максимум 32 символа |
| `min_in_team` | `int \| None` | No | |
| `max_in_team` | `int \| None` | No | |
| `hidden` | `bool \| None` | No | |
| `icon_id` | `UUID \| None` | No | |

### Result: `GameRoleItemResponse`
→ См. таблицу в контракте `role_set.role.create`.

### Behavior
1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка, что роль принадлежит набору ролей локальной игры сервера.
3. `name` и `hidden` обновляются, только если переданы и отличаются от текущих; `min_in_team`, `max_in_team`, `icon_id` — если переданы (без сравнения с текущим значением).

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу |
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |

---

## Queue: `role_set.global.role.update`

Обрабатывается `GameRoleService.update_global_role()`. Не требует `access_data`.

### Command: `GlobalGameRoleUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_id` | `UUID` | Yes | |
| `name` | `str \| None` | No | Максимум 32 символа |
| `min_in_team` | `int \| None` | No | |
| `max_in_team` | `int \| None` | No | |
| `hidden` | `bool \| None` | No | |
| `icon_id` | `UUID \| None` | No | |

### Result: `GameRoleItemResponse`
→ См. таблицу в контракте `role_set.role.create`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена |
| `ForbiddenException` | Роль принадлежит набору локальной игры |

---

## Queue: `role_set.role.icon.delete`

Обрабатывается `GameRoleService.delete_role_icon()`. Удаляет иконку роли локальной игры (устанавливает `icon_id` в `None`).

### Command: `GameRoleItemDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `role_id` | `UUID` | Yes | |

### Result: `StatusResponse`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"ok"` | |

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу |
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |

---

## Queue: `role_set.global.role.icon.delete`

Обрабатывается `GameRoleService.delete_global_role_icon()`. Не требует `access_data`.

### Command: `GlobalGameRoleDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_id` | `UUID` | Yes | |

### Result: `StatusResponse`
→ См. таблицу в контракте `role_set.role.icon.delete`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена |
| `ForbiddenException` | Роль принадлежит набору локальной игры |

---

## Queue: `role_set.role.delete`

Обрабатывается `GameRoleService.delete_role()`. Удаляет игровую роль локальной игры.

### Command: `GameRoleItemDeleteRequest`
→ См. таблицу в контракте `role_set.role.icon.delete`.

### Result: `StatusResponse`
→ См. таблицу в контракте `role_set.role.icon.delete`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу; удаление не выполнено |
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |

---

## Queue: `role_set.global.role.delete`

Обрабатывается `GameRoleService.delete_global_role()`. Не требует `access_data`.

### Command: `GlobalGameRoleDeleteRequest`
→ См. таблицу в контракте `role_set.global.role.icon.delete`.

### Result: `StatusResponse`
→ См. таблицу в контракте `role_set.role.icon.delete`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Роль не найдена; удаление не выполнено |
| `ForbiddenException` | Роль принадлежит набору локальной игры |
