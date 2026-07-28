# RatingService — Business Logic

## Overview
- **File:** `src/core/services/rating.py`
- **Private helpers:**
  - `_check_rating_set(server_id, rating_set_id) -> RatingSet` — проверяет, что набор рейтингов принадлежит серверу; выбрасывает `NotFoundException` если сервер не найден или `rating_set_id` не соответствует
  - `_check_rating(server_id, rating_id) -> Rating` — проверяет, что уровень рейтинга существует и принадлежит набору рейтингов сервера; выбрасывает `NotFoundException` если уровень не найден или не принадлежит серверу

## Dependencies

### Repositories
- `RatingRepositoryProtocol` — CRUD уровней рейтинга (`create`, `get`, `delete`, `set_threshold`, `set_icon`)
- `RatingSetRepositoryProtocol` — CRUD наборов рейтингов (`set_name`, `set_min_rating`, `set_max_rating`)
- `ServerRepositoryProtocol` — получение сервера (`get`)

## Method: `get_rating_set(server_id: UUID) -> RatingSet`

### Purpose
Возвращает набор рейтингов сервера.

### Algorithm
1. Получить сервер через `server_repo.get(server_id)` → `NotFoundException` если не найден
2. Вернуть `server.rating_set`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

## Method: `update_rating_set(server_id: UUID, rating_set_id: UUID, name: str | None, min_rating: int | None, max_rating: int | None, permission_mask: int) -> RatingSet`

### Purpose
Обновляет параметры набора рейтингов.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission через `PERMISSION.check_permission()` → `ForbiddenException` если нет прав
2. Проверить набор через `_check_rating_set(server_id, rating_set_id)` → `NotFoundException` если сервер или набор не найден
3. Если `name` передан и отличается от текущего — вызвать `rating_set_repo.set_name(rating_set, name)`
4. Если `min_rating` передан и отличается — вызвать `rating_set_repo.set_min_rating(rating_set, min_rating)`
5. Если `max_rating` передан и отличается — вызвать `rating_set_repo.set_max_rating(rating_set, max_rating)`
6. Вернуть обновлённый `rating_set`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или набор не найден |
| `ForbiddenException` | Недостаточно прав (`EDIT_RATING_SET`) |

## Method: `create_rating(server_id: UUID, rating_set_id: UUID, threshold: int, icon_id: UUID | None, permission_mask: int) -> Rating`

### Purpose
Создаёт новый уровень рейтинга в наборе.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException` если нет прав
2. Проверить набор через `_check_rating_set(server_id, rating_set_id)` → `NotFoundException` если не найден
3. Вызвать `rating_repo.create(icon_id, threshold, rating_set_id)`
4. `IntegrityForeignException` → `NotFoundException`
5. `IntegrityUnknownException` → `InternalLogicException`
6. Добавить созданный уровень в `rating_set_field.ratings`
7. Вернуть созданный `Rating`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер, набор или FK (icon_id) не найдены |
| `ForbiddenException` | Недостаточно прав (`EDIT_RATING_SET`) |
| `InternalLogicException` | Неизвестная целостностная ошибка БД |

## Method: `update_rating(server_id: UUID, rating_id: UUID, threshold: int | None, icon_id: UUID | None, permission_mask: int) -> Rating`

### Purpose
Обновляет уровень рейтинга.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException` если нет прав
2. Проверить уровень через `_check_rating(server_id, rating_id)` → `NotFoundException` если не найден
3. Если `threshold` передан и отличается — вызвать `rating_repo.set_threshold(rating, threshold)`
4. Если `icon_id` передан и отличается — вызвать `rating_repo.set_icon(rating, icon_id)`
5. Вернуть обновлённый `Rating`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или уровень не найден |
| `ForbiddenException` | Недостаточно прав (`EDIT_RATING_SET`) |

## Method: `delete_rating(server_id: UUID, rating_id: UUID, permission_mask: int) -> None`

### Purpose
Удаляет уровень рейтинга.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException` если нет прав
2. Проверить уровень через `_check_rating(server_id, rating_id)` → `NotFoundException` если не найден
3. Вызвать `rating_repo.delete(rating_id)`
4. Если `delete` вернул `False` → `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер, уровень не найден, или уровень не удалось удалить |
| `ForbiddenException` | Недостаточно прав (`EDIT_RATING_SET`) |

## Method: `delete_rating_icon(server_id: UUID, rating_id: UUID, permission_mask: int) -> Rating`

### Purpose
Удаляет иконку уровня рейтинга (устанавливает `icon_id` в `None`).

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException` если нет прав
2. Проверить уровень через `_check_rating(server_id, rating_id)` → `NotFoundException` если не найден
3. Вызвать `rating_repo.set_icon(rating, None)`
4. Вернуть обновлённый `Rating`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер или уровень не найден |
| `ForbiddenException` | Недостаточно прав (`EDIT_RATING_SET`) |
