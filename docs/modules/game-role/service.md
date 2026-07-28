# GameRoleService — Business Logic

## Overview
- **File:** `src/core/services/game_role.py`
- **Private helpers:**
  - `_set_and_game(role_set_id) -> tuple[GameRoleSet, Game]` — получает набор ролей и игру-владельца; `NotFoundException`, если набор не найден, `InternalLogicException`, если игра-владелец не найдена
  - `_require_local_set(server_id, role_set_id) -> GameRoleSet` — через `_set_and_game`, проверяет, что игра локальная и принадлежит `server_id`
  - `_require_global_set(role_set_id) -> GameRoleSet` — через `_set_and_game`, проверяет, что игра глобальная
  - `_require_local_role(server_id, role_id) -> GameRole` / `_require_global_role(role_id) -> GameRole` — получают роль и делегируют проверку набора соответствующему `_require_*_set()`
  - `_apply_role_update(role, name, min_in_team, max_in_team, icon_id, hidden) -> GameRole` — общее тело обновления, переиспользуемое `update_role` и `update_global_role`

## Dependencies

### Repositories
- `GameRoleSetRepositoryProtocol` — чтение набора ролей и его игры-владельца, обновление названия набора
- `GameRoleRepositoryProtocol` — CRUD игровых ролей
- `GameRepositoryProtocol` — определение, глобальная или локальная игра владеет набором ролей
- `ServerRepositoryProtocol` — принимается в конструкторе, но не используется в текущей реализации (принадлежность серверу определяется через `game.server_id`, а не запрос к репозиторию сервера)

---

## Method: `update_role_set(server_id, role_set_id, name=None, permission_mask=0) -> GameRoleSetDetail`

### Purpose
Обновляет название набора ролей локальной игры сервера.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException` ("Unable to edit role set")
2. `_require_local_set(server_id, role_set_id)`
3. Если `name` передан и отличается от текущего — `role_set_repo.update(GameRoleSetUpdate(id=role_set_id, name=name))`
4. Вернуть `role_set_repo.get_detail(role_set_id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре ("Unable to edit a global game role set") |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу ("Role set not found for server") |
| `InternalLogicException` | Игра-владелец набора не найдена; набор не найден после обновления |

---

## Method: `update_global_role_set(role_set_id, name=None) -> GameRoleSetDetail`

### Purpose
Обновляет название набора ролей глобальной игры. Не проверяет права — доступно только через `role_set.global.*` очереди без авторизации.

### Algorithm
1. `_require_global_set(role_set_id)` → `ForbiddenException` ("Role set does not belong to a global game"), если набор принадлежит локальной игре
2. Если `name` передан и отличается от текущего — обновить
3. Вернуть `role_set_repo.get_detail(role_set_id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден |
| `InternalLogicException` | Игра-владелец не найдена; набор не найден после обновления |

---

## Method: `create_role(server_id, role_set_id, name, min_in_team, max_in_team, icon_id=None, hidden=False, permission_mask=0) -> GameRole`

### Purpose
Создаёт новую игровую роль в наборе локальной игры сервера.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. `_require_local_set(server_id, role_set_id)`
3. `role_repo.create(GameRoleCreate(...))` → `IntegrityForeignException` → `NotFoundException`; `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Method: `create_global_role(role_set_id, name, min_in_team, max_in_team, icon_id=None, hidden=False) -> GameRole`

### Purpose
Создаёт новую игровую роль в наборе глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_set(role_set_id)`
2. `role_repo.create(GameRoleCreate(...))` → `IntegrityForeignException` → `NotFoundException`; `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Method: `update_role(server_id, role_id, name=None, min_in_team=None, max_in_team=None, icon_id=None, hidden=None, permission_mask=0) -> GameRole`

### Purpose
Обновляет параметры роли локальной игры.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. `_require_local_role(server_id, role_id)`
3. `_apply_role_update(role, name, min_in_team, max_in_team, icon_id, hidden)`:
   - `name`, `hidden` обновляются, только если переданное значение отличается от текущего
   - `min_in_team`, `max_in_team`, `icon_id` применяются, если переданы (без сравнения с текущим значением)
   - Если хотя бы одно поле изменилось — `role_repo.update(GameRoleUpdate(...))`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу |

---

## Method: `update_global_role(role_id, name=None, min_in_team=None, max_in_team=None, icon_id=None, hidden=None) -> GameRole`

### Purpose
Обновляет параметры роли глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_role(role_id)`
2. `_apply_role_update(role, name, min_in_team, max_in_team, icon_id, hidden)` (та же логика, что у `update_role`)

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Роль принадлежит набору локальной игры |
| `NotFoundException` | Роль не найдена |

---

## Method: `delete_role(server_id, role_id, permission_mask=0) -> None`

### Purpose
Удаляет игровую роль из набора локальной игры.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException` ("Unable to delete role")
2. `_require_local_role(server_id, role_id)`
3. `role_repo.delete(role_id)` → `NotFoundException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу; удаление не выполнено |

---

## Method: `delete_global_role(role_id) -> None`

### Purpose
Удаляет игровую роль из набора глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_role(role_id)`
2. `role_repo.delete(role_id)` → `NotFoundException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Роль принадлежит набору локальной игры |
| `NotFoundException` | Роль не найдена; удаление не выполнено |

---

## Method: `delete_role_icon(server_id, role_id, permission_mask=0) -> GameRole`

### Purpose
Удаляет иконку роли локальной игры (устанавливает `icon_id` в `None`).

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. `_require_local_role(server_id, role_id)`
3. `role_repo.update(GameRoleUpdate(id=role.id, icon_id=None))`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; роль принадлежит набору глобальной игры |
| `NotFoundException` | Роль не найдена; набор роли принадлежит другому серверу |

---

## Method: `delete_global_role_icon(role_id) -> GameRole`

### Purpose
Удаляет иконку роли глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_role(role_id)`
2. `role_repo.update(GameRoleUpdate(id=role.id, icon_id=None))`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Роль принадлежит набору локальной игры |
| `NotFoundException` | Роль не найдена |

---

> Метод `get_role_set_for_server` удалён — набор ролей теперь всегда доставляется вложенным внутри `GameDetail` (см. [modules/game/service.md](../game/service.md)); отдельного пути чтения набора ролей больше нет.
