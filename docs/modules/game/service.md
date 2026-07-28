# GameService — Business Logic

## Overview
- **File:** `src/core/services/game.py`
- **Private helpers:**
  - `_create_game_shell(name, min_rating, max_rating, icon_id, banner_id, server_id) -> tuple[Game, GameRoleSet, RatingSet]` — проверяет `min_rating <= max_rating`, создаёт `Game` + пустой `role_set` + `rating_set` (без ролей)
  - `_build_game(name, min_rating, max_rating, icon_id, banner_id, server_id) -> GameDetail` — `_create_game_shell` плюс автосоздание роли «Leader» (`min_in_team = max_in_team = 1`, `hidden = False`); возвращает полный `GameDetail`
  - `_require_global(game_id) -> Game` — получает игру и проверяет, что она глобальная
  - `_require_local(server_id, game_id) -> Game` — получает игру и проверяет, что она локальная и принадлежит указанному серверу
  - `_assert_selectable(server_id, game_ids) -> None` — для каждого `game_id` проверяет, что игра существует и является либо глобальной, либо локальной игрой того же сервера (не даёт подключить чужую локальную игру)

## Dependencies

### Repositories
- `GameRepositoryProtocol` — CRUD игр, вложенные `get_detail`-чтения, управление связями с сервером (`server_game`)
- `ServerRepositoryProtocol` — проверка существования сервера
- `GameRoleSetRepositoryProtocol` — создание набора ролей при создании игры
- `RatingSetRepositoryProtocol` — создание набора рейтингов при создании игры
- `GameRoleRepositoryProtocol` — создание роли «Leader»; копирование ролей при копировании игры
- `RatingRepositoryProtocol` — копирование уровней рейтинга при копировании игры

---

## Method: `list_global_games() -> list[GameDetail]`

### Purpose
Возвращает список всех глобальных игр с вложенными наборами ролей и рейтингов.

### Algorithm
1. Вызвать `game_repo.list_global()`

---

## Method: `create_global_game(name, min_rating, max_rating, icon_id=None, banner_id=None) -> GameDetail`

### Purpose
Создаёт глобальную игру. Не проверяет права — доступно только через `game.global.*` очереди без авторизации (gateway ограничивает доступ сайт-админом).

### Algorithm
1. Вызвать `_build_game(name, min_rating, max_rating, icon_id, banner_id, server_id=None)`:
   1. Проверить `min_rating <= max_rating` → `BadRequestException`, если нарушено
   2. Создать `Game` через `game_repo.create()` → `IntegrityUniqueException` → `BadRequestException`; `IntegrityForeignException` → `NotFoundException`; `IntegrityUnknownException` → `InternalLogicException`
   3. Создать `GameRoleSet` (`name` = имя игры) через `game_role_set_repo.create()`
   4. Создать роль «Leader» через `game_role_repo.create()`
   5. Создать `RatingSet` (`name` = имя игры, переданные границы) через `rating_set_repo.create()`
   6. Вернуть `game_repo.get_detail(game.id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `BadRequestException` | `min_rating > max_rating`; название игры уже занято среди глобальных |
| `NotFoundException` | Нарушение внешнего ключа при создании (`IntegrityForeignException`) |
| `InternalLogicException` | Прочая ошибка целостности БД; вложенная игра не найдена после создания |

---

## Method: `update_global_game(game_id, name=None, icon_id=None, banner_id=None) -> GameDetail`

### Purpose
Обновляет глобальную игру.

### Algorithm
1. `_require_global(game_id)` → `NotFoundException`, если игра не найдена; `ForbiddenException`, если у игры указан `server_id`
2. Собрать `update_data` из полей, отличающихся от текущих значений игры
3. Если `update_data` не пуст — `game_repo.update(GameUpdate(id=game_id, **update_data))` → `IntegrityUniqueException` → `BadRequestException`
4. Вернуть `game_repo.get_detail(game_id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена |
| `ForbiddenException` | `game_id` указывает на локальную игру ("Game is not a global game") |
| `BadRequestException` | Название игры уже занято среди глобальных |
| `InternalLogicException` | Игра не найдена после обновления |

---

## Method: `delete_global_game(game_id) -> None`

### Purpose
Удаляет глобальную игру, каскадно удаляя её `role_set`/`rating_set` (и вложенные роли/рейтинги).

### Algorithm
1. `_require_global(game_id)`
2. `game_repo.delete(game_id)` → `InternalLogicException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Игра не найдена |
| `ForbiddenException` | `game_id` указывает на локальную игру |
| `InternalLogicException` | Удаление не выполнено |

---

## Method: `list_server_games(server_id) -> list[GameDetail]`

### Purpose
Возвращает список игр, подключённых к серверу (глобальных и локальных), с вложенными наборами.

### Algorithm
1. Проверить существование сервера через `server_repo.get(server_id)` → `NotFoundException`
2. Вернуть `game_repo.list_for_server(server_id)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Method: `list_owned_games(server_id) -> list[GameDetail]`

### Purpose
Возвращает список локальных игр, принадлежащих серверу (`server_id = сервер`), независимо от того, подключены ли они через `server_game`.

### Algorithm
1. Проверить существование сервера → `NotFoundException`
2. Вернуть `game_repo.list_owned_by_server(server_id)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Method: `create_local_game(server_id, name, min_rating, max_rating, icon_id=None, banner_id=None, permission_mask=0) -> GameDetail`

### Purpose
Создаёт локальную игру для сервера и сразу подключает её к нему.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. Проверить существование сервера → `NotFoundException`
3. `_build_game(name, min_rating, max_rating, icon_id, banner_id, server_id=server_id)` — создаёт игру с ролью «Leader»
4. Подключить игру к серверу через `game_repo.add_to_server(detail.id, server_id)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (`EDIT_SERVER_GAME`) |
| `NotFoundException` | Сервер не найден |
| `BadRequestException` | `min_rating > max_rating`; имя игры уже занято на сервере |
| `InternalLogicException` | Ошибка целостности при создании |

---

## Method: `copy_global_game(server_id, game_id, permission_mask=0) -> GameDetail`

### Purpose
Копирует глобальную игру в воркспейс как полностью независимую локальную игру со всеми её ролями и уровнями рейтинга.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. Проверить существование сервера → `NotFoundException`
3. Получить исходную игру через `game_repo.get_detail(game_id)` → `NotFoundException`, если `None`; `ForbiddenException`, если `source.server_id is not None`
4. Создать «пустую» локальную игру-оболочку через `_create_game_shell(source.name, source.rating_set.min_rating, source.rating_set.max_rating, source.icon_id, source.banner_id, server_id=server_id)` — **без** авто-роли «Leader»
5. Скопировать каждую роль `source.role_set.game_roles` через `game_role_repo.copy_role(role, new_role_set.id)`
6. Скопировать каждый уровень `source.rating_set.ratings` через `rating_repo.copy_rating(rating, new_rating_set.id)`
7. Подключить новую игру к серверу через `game_repo.add_to_server(new_game.id, server_id)`
8. Вернуть `game_repo.get_detail(new_game.id)` → `InternalLogicException`, если `None`

### Behavior
- Копия не получает дублирующую роль «Leader» — переносятся ровно те роли, что были у исходной игры, включая пустой набор ролей.
- Копия полностью независима: последующие изменения оригинальной глобальной игры не затрагивают копию.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав (`EDIT_SERVER_GAME`); `game_id` указывает на локальную (не глобальную) игру |
| `NotFoundException` | Сервер или исходная игра не найдены |
| `BadRequestException` | Имя исходной игры уже занято локально на сервере |
| `InternalLogicException` | Копия не найдена после создания |

---

## Method: `update_local_game(server_id, game_id, name=None, icon_id=None, banner_id=None, permission_mask=0) -> GameDetail`

### Purpose
Обновляет локальную игру сервера.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. `_require_local(server_id, game_id)` → `NotFoundException`, если игра не существует или принадлежит другому серверу; `ForbiddenException`, если игра глобальная
3. Собрать `update_data` из отличающихся полей, обновить при необходимости → `IntegrityUniqueException` → `BadRequestException`
4. Вернуть `game_repo.get_detail(game_id)` → `InternalLogicException`, если `None`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; `game_id` указывает на глобальную игру ("Unable to edit a global game") |
| `NotFoundException` | Игра не найдена; игра принадлежит другому серверу ("Game not found on server") |
| `BadRequestException` | Имя игры уже занято на сервере |
| `InternalLogicException` | Игра не найдена после обновления |

---

## Method: `delete_local_game(server_id, game_id, permission_mask=0) -> None`

### Purpose
Удаляет локальную игру сервера, каскадно удаляя её `role_set`/`rating_set`.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. `_require_local(server_id, game_id)`
3. `game_repo.delete(game_id)` → `InternalLogicException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав; игра глобальная |
| `NotFoundException` | Игра не найдена; принадлежит другому серверу |
| `InternalLogicException` | Удаление не выполнено |

---

## Method: `add_games_to_server(server_id, game_ids, permission_mask=0) -> None`

### Purpose
Подключает список игр (глобальных и/или собственных локальных) к серверу.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. Если `game_ids` пуст — досрочный возврат
3. `_assert_selectable(server_id, game_ids)` → `NotFoundException` для несуществующей игры или локальной игры другого сервера
4. `game_repo.bulk_add_to_server(server_id, game_ids)` → `IntegrityForeignException` → `NotFoundException`; `IntegrityUniqueException`/`IntegrityUnknownException` → `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав |
| `NotFoundException` | Одна из игр не найдена или является локальной игрой другого сервера |
| `InternalLogicException` | Ошибка целостности данных |

---

## Method: `remove_game_from_server(server_id, game_id, permission_mask=0) -> None`

### Purpose
Отключает игру от сервера.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. `game_repo.remove_from_server(game_id, server_id)` → `NotFoundException`, если `False`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав |
| `NotFoundException` | Игра не найдена на сервере |

---

## Method: `set_server_games(server_id, game_ids, permission_mask=0) -> None`

### Purpose
Полностью заменяет список подключённых игр сервера.

### Algorithm
1. Проверить `EDIT_SERVER_GAME` permission → `ForbiddenException`
2. `_assert_selectable(server_id, game_ids)` → `NotFoundException` для несуществующей игры или локальной игры другого сервера
3. `game_repo.set_server_games(server_id, game_ids)`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `ForbiddenException` | Недостаточно прав |
| `NotFoundException` | Одна из игр не найдена или является локальной игрой другого сервера |
