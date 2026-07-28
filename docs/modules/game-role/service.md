# GameRoleService — Business Logic

## Overview
- **File:** `src/core/services/game_role.py`
- **Private helper:** `_check_role_belongs_to_server(role_id: UUID, server_id: UUID) -> GameRole` — проверяет, что роль принадлежит серверу: получает сервер и роль, сверяет `role_set_id` роли с `id` набора сервера

## Dependencies

### Repositories
- `ServerRepositoryProtocol` — получение сервера и его набора ролей
- `GameRoleSetRepositoryProtocol` — изменение названия набора ролей (`set_name`)
- `GameRoleRepositoryProtocol` — CRUD игровых ролей и точечное обновление полей (`set_name`, `set_hidden`, `set_min`, `set_max`, `set_icon`)

---

## Method: `get_role_set_for_server(server_id: UUID) -> GameRoleSet`

### Purpose
Возвращает набор ролей сервера.

### Algorithm
1. Получить сервер по `server_id` → `NotFoundException`, если не найден
2. Вернуть `server.role_set`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Method: `update_role_set(role_set_id: UUID, server_id: UUID, name: str | None = None, permission_mask: int = 0) -> GameRoleSet`

### Purpose
Обновляет название набора ролей сервера.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission через `PERMISSION.check_permission()` → `ForbiddenException`
2. Получить сервер по `server_id` → `NotFoundException`
3. Извлечь набор ролей из `server.role_set`; если отсутствует или `id` не совпадает с `role_set_id` → `NotFoundException`
4. Если `name` указан и отличается от текущего — вызвать `role_set_repo.set_name(role_set_field, name)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден или набор ролей не найден для сервера |
| `ForbiddenException` | Недостаточно прав (отсутствует `EDIT_ROLE_SET`) |

---

## Method: `create_role(role_set_id: UUID, server_id: UUID, name: str, min_in_team: int, max_in_team: int, icon_id: UUID | None = None, hidden: bool = False, permission_mask: int = 0) -> GameRole`

### Purpose
Создаёт новую игровую роль в наборе ролей сервера.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. Получить сервер по `server_id` → `NotFoundException`
3. Извлечь набор ролей сервера; если отсутствует или `id` не совпадает с `role_set_id` → `NotFoundException`
4. Вызвать `role_repo.create(name, role_set_id, min_in_team, max_in_team, icon_id, hidden)`
   - Перехватить `IntegrityForeignException` → `NotFoundException`
   - Перехватить `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден, набор ролей не найден, или FK-ограничение (`IntegrityForeignException`) |
| `ForbiddenException` | Недостаточно прав (отсутствует `EDIT_ROLE_SET`) |
| `InternalLogicException` | Неизвестная ошибка целостности (`IntegrityUnknownException`) |

---

## Method: `update_role(role_id: UUID, server_id: UUID, name: str | None = None, min_in_team: int | None = None, max_in_team: int | None = None, icon_id: UUID | None = None, hidden: bool | None = None, permission_mask: int = 0) -> GameRole`

### Purpose
Обновляет параметры существующей игровой роли. Изменяются только переданные поля.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. Получить роль через `_check_role_belongs_to_server()` → `NotFoundException`
3. Для каждого переданного поля, если значение изменилось — вызвать соответствующий `role_repo.set_*()`:
   - `name` — `role_repo.set_name()`
   - `hidden` — `role_repo.set_hidden()`
   - `min_in_team` — `role_repo.set_min()`
   - `max_in_team` — `role_repo.set_max()`
   - `icon_id` — `role_repo.set_icon()`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены; роль не принадлежит указанному серверу |
| `ForbiddenException` | Недостаточно прав (отсутствует `EDIT_ROLE_SET`) |

---

## Method: `delete_role(role_id: UUID, server_id: UUID, permission_mask: int = 0) -> None`

### Purpose
Удаляет игровую роль из набора.

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. Получить роль через `_check_role_belongs_to_server()` → `NotFoundException`
3. Вызвать `role_repo.delete(role_id)`. Если удаление не выполнено → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены; роль не удалена (не существовала) |
| `ForbiddenException` | Недостаточно прав (отсутствует `EDIT_ROLE_SET`) |

---

## Method: `delete_role_icon(role_id: UUID, server_id: UUID, permission_mask: int = 0) -> GameRole`

### Purpose
Удаляет иконку игровой роли (устанавливает `icon_id` в `None`).

### Algorithm
1. Проверить `EDIT_ROLE_SET` permission → `ForbiddenException`
2. Получить роль через `_check_role_belongs_to_server()` → `NotFoundException`
3. Вызвать `role_repo.set_icon(role_field, None)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или роль не найдены; роль не принадлежит серверу |
| `ForbiddenException` | Недостаточно прав (отсутствует `EDIT_ROLE_SET`) |
