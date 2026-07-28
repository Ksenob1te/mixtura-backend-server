# ServerRepository

**Protocol:** `src/core/interfaces/repo/server.py`
**Implementation:** `src/infra/postgre/repo/server.py`
**Model:** [Server](../models/server.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(server_id: UUID, /) -> Server \| None` | |
| `delete` | `(server_id: UUID, /) -> bool` | |

## Custom Methods

### `create(name, owner_id, public, description, icon_id, banner_id) -> Server`
Создаёт новый сервер. Проверяет целостность внешнего ключа `owner_id`; при нарушении выбрасывает `IntegrityForeignException`. После flush повторно загружает созданную запись через `get`.

### `list_public(page, name_filter, page_size) -> Sequence[Server]`
Список публичных серверов (`public == True`) с пагинацией и необязательной фильтрацией по названию (`ILIKE`).

### `list_by_owner(owner_id, page, name_filter, page_size) -> Sequence[Server]`
Список серверов, принадлежащих указанному пользователю (`owner_id`).

### `list_by_user(user_id, page, name_filter, page_size) -> Sequence[Server]`
Список серверов, где указанный пользователь является активным участником. Фильтрует через отношение `Server.members` с условием `Member.active == True`.

### `set_name(server, name) -> Server`
Устанавливает название сервера.

### `set_description(server, description) -> Server`
Устанавливает описание сервера.

### `set_public(server, public) -> Server`
Устанавливает флаг публичности сервера.

### `set_icon(server, icon_id) -> Server`
Устанавливает иконку сервера. `icon_id` может быть `None` для сброса.

### `set_banner(server, banner_id) -> Server`
Устанавливает баннер сервера. `banner_id` может быть `None` для сброса.
