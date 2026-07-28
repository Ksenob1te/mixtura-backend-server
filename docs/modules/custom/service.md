# MemberCustomService — Business Logic

## Overview
- **File:** `src/core/services/member_custom.py`

## Dependencies

### Repositories
- `CustomRepositoryProtocol` — CRUD кастомных списков
- `CustomRatingRepositoryProtocol` — CRUD оценок ролей в кастомных списках
- `MemberRepositoryProtocol` — получение участников
- `GameRoleRepositoryProtocol` — получение игровых ролей
- `ServerRepositoryProtocol` — получение сервера участника
- `RatingSetRepositoryProtocol` — получение набора рейтингов игры по `game_id` (`get_by_game_id`)
- `GameRoleSetRepositoryProtocol` — получение набора ролей, которому принадлежит игровая роль
- `GameRepositoryProtocol` — проверка, что игра подключена к серверу участника (`is_enabled_on_server`)

## Method: `list_customs(server_id, member_id) -> list[Custom]`

### Purpose
Возвращает все кастомные списки указанного участника в рамках сервера.

### Algorithm
1. Получить участника через `member_repo.get(member_id)`
2. Если участник не найден или `member.server_id != server_id` → `NotFoundException`
3. Вызвать `custom_repo.list_for_member(member_id)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Участник не найден или не принадлежит серверу |

---

## Method: `create_custom(issuer_id, server_id, member_id, permission_mask) -> Custom`

### Purpose
Создаёт пустой кастомный список для целевого участника от имени инициатора.

### Algorithm
1. Проверить `CREATE_CUSTOM` permission → `ForbiddenException`
2. Получить целевого участника через `member_repo.get(member_id)`
3. Если участник не найден или `member.server_id != server_id` → `NotFoundException`
4. Вызвать `custom_repo.create(member_id=member_id, creator_id=issuer_id)`
5. `IntegrityForeignException` → `NotFoundException`
6. `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Целевой участник не найден; issuer (создатель) не найден в БД |
| `ForbiddenException` | Недостаточно прав (требуется `CREATE_CUSTOM`) |
| `InternalLogicException` | Ошибка создания записи в БД |

---

## Method: `get_custom(server_id, custom_id) -> Custom`

### Purpose
Возвращает кастомный список по ID с проверкой принадлежности к серверу.

### Algorithm
1. Получить custom через `custom_repo.get(custom_id)`
2. Если `custom.member is None` → `InternalLogicException`
3. Если custom не найден или `custom.member.server_id != server_id` → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Кастомный список не найден или не принадлежит серверу |
| `InternalLogicException` | Участник-владелец списка отсутствует в БД |

---

## Method: `delete_custom(server_id, custom_id, permission_mask) -> None`

### Purpose
Удаляет кастомный список.

### Algorithm
1. Проверить `DELETE_CUSTOM` permission → `ForbiddenException`
2. Вызвать `get_custom(server_id, custom_id)` — валидирует существование и принадлежность → `NotFoundException`, `InternalLogicException`
3. Вызвать `custom_repo.delete(custom_id)`
4. Если результат `False` → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Кастомный список не найден или не принадлежит серверу |
| `ForbiddenException` | Недостаточно прав (требуется `DELETE_CUSTOM`) |
| `InternalLogicException` | Участник-владелец списка отсутствует в БД |

---

## Method: `set_rating_value(issuer_id, server_id, custom_id, game_role_id, rating, permission_mask) -> Custom`

### Purpose
Устанавливает или обновляет оценку игровой роли в кастомном списке.

### Algorithm
1. Получить custom через `get_custom(server_id, custom_id)` → `NotFoundException`, `InternalLogicException`
2. Проверить права: `custom.creator_id != issuer_id` и нет `EDIT_ALL_CUSTOMS` → `ForbiddenException`
3. Получить участника-владельца custom через `member_repo.get(custom.member_id)`; если `None` → `InternalLogicException`
4. Получить сервер участника через `server_repo.get(member.server_id)`; если `None` → `InternalLogicException`
5. Получить игровую роль через `game_role_repo.get(game_role_id)` → `NotFoundException`, если не найдена
6. Получить набор ролей роли через `game_role_set_repo.get(role.role_set_id)` → `InternalLogicException`, если не найден
7. Проверить, что игра набора ролей подключена к серверу участника через `game_repo.is_enabled_on_server(server_id, role_set.game_id)` → `NotFoundException` ("Game is not enabled on server"), если `False`
8. Получить набор рейтингов игры через `rating_set_repo.get_by_game_id(role_set.game_id)` → `InternalLogicException`, если `None`
9. Проверить `rating` в диапазоне `[rating_set.min_rating, rating_set.max_rating]` → `BadRequestException`
10. Попробовать получить существующую оценку: `custom_rating_repo.get_by_custom_role(custom_id, game_role_id)`
11. Если оценка существует: обновить через `custom_rating_repo.update(CustomRatingUpdate(id=existing.id, rating=rating))`
12. Если не существует: создать `custom_rating_repo.create(CustomRatingCreate(custom_id=custom_id, game_role_id=game_role_id, rating=rating))`
    - `IntegrityForeignException` → `NotFoundException`
    - `IntegrityUniqueException` → `InternalLogicException`
    - `IntegrityUnknownException` → `InternalLogicException`

### Behavior
- Границы рейтинга определяются набором рейтингов **игры**, которой принадлежит `game_role_id` — не сервера. `Custom` не привязан к одной игре: он может хранить оценки ролей из разных игр, подключённых к серверу, каждая проверяется по границам своей игры.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Кастомный список не найден; игровая роль не найдена; игра роли не подключена к серверу участника ("Game is not enabled on server") |
| `ForbiddenException` | Участник не является создателем списка и не имеет права `EDIT_ALL_CUSTOMS` |
| `BadRequestException` | Значение `rating` вне диапазона `[min_rating, max_rating]` набора рейтингов игры |
| `InternalLogicException` | Участник или сервер для custom не найдены; набор ролей или набор рейтингов игры не найдены; нарушение уникальности при создании оценки |
