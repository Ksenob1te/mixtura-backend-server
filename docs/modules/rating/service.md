# RatingService — Business Logic

## Overview
- **File:** `src/core/services/rating.py`
- **Private helpers:**
  - `_set_and_game(rating_set_id) -> tuple[RatingSet, Game]` — получает набор рейтингов и игру-владельца; `NotFoundException`, если набор не найден, `InternalLogicException`, если игра-владелец не найдена
  - `_require_local_set(server_id, rating_set_id) -> RatingSet` — через `_set_and_game`, проверяет, что игра локальная и принадлежит `server_id`
  - `_require_global_set(rating_set_id) -> RatingSet` — через `_set_and_game`, проверяет, что игра глобальная
  - `_require_local_rating(server_id, rating_id) -> Rating` / `_require_global_rating(rating_id) -> Rating` — получают уровень рейтинга и делегируют проверку набора соответствующему `_require_*_set()`
  - `_build_rating_set_update_data(current, name, min_rating, max_rating) -> dict` — собирает поля, отличающиеся от текущих значений набора
  - `_assert_bounds_valid(update_data, current) -> None` — проверяет `min_rating <= max_rating` по эффективным границам (учитывая ещё не применённый `update_data`) → `BadRequestException`, если нарушено
  - `_apply_rating_set_update(rating_set_id, current, name, min_rating, max_rating) -> RatingSetDetail` — общее тело, переиспользуемое `update_rating_set` и `update_global_rating_set`
  - `_apply_rating_update(rating, threshold, icon_id) -> Rating` — общее тело, переиспользуемое `update_rating` и `update_global_rating`

## Dependencies

### Repositories
- `RatingRepositoryProtocol` — CRUD уровней рейтинга
- `RatingSetRepositoryProtocol` — чтение набора рейтингов и его игры-владельца, обновление параметров набора
- `GameRepositoryProtocol` — определение, глобальная или локальная игра владеет набором рейтингов
- `ServerRepositoryProtocol` — принимается в конструкторе, но не используется в текущей реализации (принадлежность серверу определяется через `game.server_id`, а не запрос к репозиторию сервера)

---

## Method: `update_rating_set(server_id, rating_set_id, name=None, min_rating=None, max_rating=None, permission_mask=0) -> RatingSetDetail`

### Purpose
Обновляет параметры набора рейтингов локальной игры сервера.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException` ("Unable to edit rating set")
2. `_require_local_set(server_id, rating_set_id)`
3. `_apply_rating_set_update(rating_set_id, rating_set, name, min_rating, max_rating)`:
   1. Собрать `update_data` из полей (`name`, `min_rating`, `max_rating`), отличающихся от текущих
   2. Проверить эффективные границы (`update_data`, применённый поверх текущего набора) → `BadRequestException` ("Rating bounds are invalid"), если `min > max`
   3. Если `update_data` не пуст — `rating_set_repo.update(RatingSetUpdate(...))`
   4. Вернуть `rating_set_repo.get_detail(rating_set_id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре ("Unable to edit a global game rating set") |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу |
| `BadRequestException` | Эффективные `min_rating` > `max_rating` |
| `InternalLogicException` | Игра-владелец не найдена; набор не найден после обновления |

---

## Method: `update_global_rating_set(rating_set_id, name=None, min_rating=None, max_rating=None) -> RatingSetDetail`

### Purpose
Обновляет параметры набора рейтингов глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_set(rating_set_id)` → `ForbiddenException` ("Rating set does not belong to a global game"), если набор принадлежит локальной игре
2. `_apply_rating_set_update(...)` — та же логика диффинга и проверки границ, что и у `update_rating_set`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден |
| `BadRequestException` | Эффективные `min_rating` > `max_rating` |
| `InternalLogicException` | Игра-владелец не найдена; набор не найден после обновления |

---

## Method: `create_rating(server_id, rating_set_id, threshold, icon_id=None, permission_mask=0) -> Rating`

### Purpose
Создаёт новый уровень рейтинга в наборе локальной игры.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException`
2. `_require_local_set(server_id, rating_set_id)`
3. `rating_repo.create(RatingCreate(...))` → `IntegrityForeignException` → `NotFoundException`; `IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; набор принадлежит глобальной игре |
| `NotFoundException` | Набор не найден; набор принадлежит другому серверу; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Method: `create_global_rating(rating_set_id, threshold, icon_id=None) -> Rating`

### Purpose
Создаёт новый уровень рейтинга в наборе глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_set(rating_set_id)`
2. `rating_repo.create(RatingCreate(...))` → та же обработка исключений

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Набор принадлежит локальной игре |
| `NotFoundException` | Набор не найден; FK-ограничение |
| `InternalLogicException` | Неизвестная ошибка целостности |

---

## Method: `update_rating(server_id, rating_id, threshold=None, icon_id=None, permission_mask=0) -> Rating`

### Purpose
Обновляет уровень рейтинга локальной игры.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException`
2. `_require_local_rating(server_id, rating_id)`
3. `_apply_rating_update(rating, threshold, icon_id)` — обновляет только переданные и изменившиеся поля

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу |

---

## Method: `update_global_rating(rating_id, threshold=None, icon_id=None) -> Rating`

### Purpose
Обновляет уровень рейтинга глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_rating(rating_id)`
2. `_apply_rating_update(rating, threshold, icon_id)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден |

---

## Method: `delete_rating(server_id, rating_id, permission_mask=0) -> None`

### Purpose
Удаляет уровень рейтинга локальной игры.

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException`
2. `_require_local_rating(server_id, rating_id)`
3. `rating_repo.delete(rating_id)` → `NotFoundException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу; удаление не выполнено |

---

## Method: `delete_global_rating(rating_id) -> None`

### Purpose
Удаляет уровень рейтинга глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_rating(rating_id)`
2. `rating_repo.delete(rating_id)` → `NotFoundException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден; удаление не выполнено |

---

## Method: `delete_rating_icon(server_id, rating_id, permission_mask=0) -> Rating`

### Purpose
Удаляет иконку уровня рейтинга локальной игры (устанавливает `icon_id` в `None`).

### Algorithm
1. Проверить `EDIT_RATING_SET` permission → `ForbiddenException`
2. `_require_local_rating(server_id, rating_id)`
3. `rating_repo.update(RatingUpdate(id=rating.id, icon_id=None))`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; уровень принадлежит набору глобальной игры |
| `NotFoundException` | Уровень не найден; набор уровня принадлежит другому серверу |

---

## Method: `delete_global_rating_icon(rating_id) -> Rating`

### Purpose
Удаляет иконку уровня рейтинга глобальной игры. Не проверяет права.

### Algorithm
1. `_require_global_rating(rating_id)`
2. `rating_repo.update(RatingUpdate(id=rating.id, icon_id=None))`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Уровень принадлежит набору локальной игры |
| `NotFoundException` | Уровень не найден |

---

> Метод `get_rating_set` удалён — набор рейтингов теперь всегда доставляется вложенным внутри `GameDetail` (см. [modules/game/service.md](../game/service.md)); отдельного пути чтения набора рейтингов больше нет.
