# MemberCustomService — Business Logic

## Overview
- **File:** `src/core/services/member_custom.py`

## Dependencies

### Repositories
- `CustomRepositoryProtocol` — CRUD кастомных списков
- `CustomRatingRepositoryProtocol` — CRUD оценок ролей в кастомных списках
- `MemberRepositoryProtocol` — получение участников
- `GameRoleRepositoryProtocol` — получение игровых ролей

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
3. Получить `custom.member.server`; если `None` → `InternalLogicException`
4. Получить `server.rating_set`; если `None` → `InternalLogicException`
5. Проверить `rating` в диапазоне `[rating_set.min_rating, rating_set.max_rating]` → `BadRequestException`
6. Попробовать получить существующую оценку: `custom_rating_repo.get_by_custom_role(custom_id, game_role_id)`
7. Если оценка существует: обновить через `custom_rating_repo.set_rating(existing, rating)`
8. Если не существует: создать `custom_rating_repo.create(custom_id, game_role_id, rating)`
   - `IntegrityForeignException` → `NotFoundException`
   - `IntegrityUniqueException` → `InternalLogicException`
   - `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Кастомный список или игровая роль не найдены |
| `ForbiddenException` | Участник не является создателем списка и не имеет права `EDIT_ALL_CUSTOMS` |
| `BadRequestException` | Значение `rating` вне допустимого диапазона рейтинг-сета сервера |
| `InternalLogicException` | Ошибка целостности данных (сервер/рейтинг-сет отсутствуют, нарушение уникальности) |
