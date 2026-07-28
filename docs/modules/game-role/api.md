# Game Role — Queue Contracts

## Overview

- **Handler file:** `src/app/rabbit/api/game_role.py`
- **Service files:**
  - `src/core/services/game_role.py` — основная логика работы с наборами ролей и игровыми ролями
  - `src/core/services/core.py` — глобальные шаблоны ролей (`role_set.get_global`)
- **Commands file:** `src/core/commands/game_role.py`
- **Request/Response models:** `src/app/rabbit/models/game_role.py`

Обработчики используют `ResponseMessage[T]` в качестве конверта ответа (см. [Response Envelope](../../_shared/response-wrapper.md)). Для авторизации используется `AccessDataRequest`, передаваемый в теле запроса (см. [Access Data](../../_shared/access-data.md)).

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `role_set.get_global` | *(пустая команда)* | `list[GameRoleSetResponse]` | Глобальные шаблоны ролей |
| `role_set.get_by_server` | `GetServerGameRoleSetsRequest` | `GameRoleSetResponse` | Набор ролей сервера |
| `role_set.update` | `GameRoleSetUpdateRequest` | `GameRoleSetResponse` | Обновление набора ролей |
| `role_set.role.create` | `GameRoleItemCreateRequest` | `GameRoleItemResponse` | Создание игровой роли |
| `role_set.role.update` | `GameRoleItemUpdateRequest` | `GameRoleItemResponse` | Обновление игровой роли |
| `role_set.role.icon.delete` | `GameRoleItemDeleteRequest` | `StatusResponse` | Удаление иконки роли |
| `role_set.role.delete` | `GameRoleItemDeleteRequest` | `StatusResponse` | Удаление игровой роли |

## Общие исключения

| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер, набор ролей или роль не найдены |
| `ForbiddenException` | Недостаточно прав — требуется `PERMISSION.EDIT_ROLE_SET` |

---

## Queue: `role_set.get_global`

Обрабатывается `CoreService.get_global_role_templates()`. Возвращает список глобальных шаблонов наборов ролей, доступных всем серверам. Не требует авторизации.

### Command

Пустая команда (без полей).

### Result: `list[GameRoleSetResponse]`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор набора ролей |
| `name` | `str` | Название набора |
| `game_roles` | `list[GameRoleItemResponse]` | Список ролей в наборе |

---

## Queue: `role_set.get_by_server`

Обрабатывается `GameRoleService.get_role_set_for_server()`. Возвращает набор ролей, привязанный к серверу.

### Command: `GetServerGameRoleSetsRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |

### Result: `GameRoleSetResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор набора ролей |
| `name` | `str` | Название набора |
| `game_roles` | `list[GameRoleItemResponse]` | Список ролей в наборе |

---

## Queue: `role_set.update`

Обрабатывается `GameRoleService.update_role_set()`. Обновляет название набора ролей сервера.

### Behavior

1. Проверка прав `EDIT_ROLE_SET`.
2. Поиск сервера по `access_data.server_id`. Если не найден — `NotFoundException`.
3. Проверка, что `role_set_id` совпадает с набором ролей сервера. Иначе — `NotFoundException`.
4. Если `name` передан и отличается от текущего — вызов `role_set_repo.set_name()`.

### Command: `GameRoleSetUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str \| None` | No | Новое название (максимум 32 символа) |

### Result: `GameRoleSetResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор набора ролей |
| `name` | `str` | Название набора |
| `game_roles` | `list[GameRoleItemResponse]` | Список ролей в наборе |

---

## Queue: `role_set.role.create`

Обрабатывается `GameRoleService.create_role()`. Создаёт новую игровую роль в указанном наборе.

### Behavior

1. Проверка прав `EDIT_ROLE_SET`.
2. Поиск сервера. Если не найден — `NotFoundException`.
3. Проверка, что `role_set_id` совпадает с набором ролей сервера. Иначе — `NotFoundException`.
4. Создание роли через `role_repo.create()`. При `IntegrityForeignException` оборачивается в `NotFoundException`; при `IntegrityUnknownException` — в `InternalLogicException`.

### Command: `GameRoleItemCreateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |
| `role_set_id` | `UUID` | Yes | Идентификатор набора ролей |
| `name` | `str` | Yes | Название роли (максимум 32 символа) |
| `min_in_team` | `int` | Yes | Минимальное количество в команде |
| `max_in_team` | `int` | Yes | Максимальное количество в команде |
| `hidden` | `bool` | No | Скрытая роль (по умолчанию `False`) |
| `icon_id` | `UUID \| None` | No | Идентификатор иконки |

### Result: `GameRoleItemResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор роли |
| `name` | `str` | Название роли |
| `icon_id` | `UUID \| None` | Идентификатор иконки |
| `min_in_team` | `int` | Минимальное количество в команде |
| `max_in_team` | `int` | Максимальное количество в команде |
| `hidden` | `bool` | Флаг скрытой роли |

---

## Queue: `role_set.role.update`

Обрабатывается `GameRoleService.update_role()`. Обновляет поля игровой роли. Обновляются только переданные (не `None`) поля.

### Behavior

1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка принадлежности роли серверу через `_check_role_belongs_to_server()`. Если сервер или роль не найдены, или роль не принадлежит набору сервера — `NotFoundException`.
3. Обновление полей по отдельности через репозиторий: `set_hidden`, `set_min`, `set_max`, `set_icon`, а также `name` если передан.

### Command: `GameRoleItemUpdateRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |
| `role_id` | `UUID` | Yes | Идентификатор роли |
| `name` | `str \| None` | No | Название (максимум 32 символа) |
| `min_in_team` | `int \| None` | No | Минимальное количество в команде |
| `max_in_team` | `int \| None` | No | Максимальное количество в команде |
| `hidden` | `bool \| None` | No | Флаг скрытой роли |
| `icon_id` | `UUID \| None` | No | Идентификатор иконки |

### Result: `GameRoleItemResponse`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Идентификатор роли |
| `name` | `str` | Название роли |
| `icon_id` | `UUID \| None` | Идентификатор иконки |
| `min_in_team` | `int` | Минимальное количество в команде |
| `max_in_team` | `int` | Максимальное количество в команде |
| `hidden` | `bool` | Флаг скрытой роли |

---

## Queue: `role_set.role.icon.delete`

Обрабатывается `GameRoleService.delete_role_icon()`. Удаляет иконку роли (устанавливает `icon_id` в `None`).

### Behavior

1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка принадлежности роли серверу через `_check_role_belongs_to_server()`. Если не найдена — `NotFoundException`.
3. Установка `icon_id` в `None` через `role_repo.set_icon()`.

### Command: `GameRoleItemDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |
| `role_id` | `UUID` | Yes | Идентификатор роли |

### Result: `StatusResponse`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"ok"` | Статус операции |

---

## Queue: `role_set.role.delete`

Обрабатывается `GameRoleService.delete_role()`. Удаляет игровую роль.

### Behavior

1. Проверка прав `EDIT_ROLE_SET`.
2. Проверка принадлежности роли серверу через `_check_role_belongs_to_server()`. Если не найдена — `NotFoundException`.
3. Вызов `role_repo.delete()`. Если роль не найдена (удалена в ходе конкурентного доступа) — `NotFoundException`.

### Command: `GameRoleItemDeleteRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Данные авторизации |
| `role_id` | `UUID` | Yes | Идентификатор роли |

### Result: `StatusResponse`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `str` | `"ok"` | Статус операции |
