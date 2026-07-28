# MemberRepository

**Protocol:** `src/core/interfaces/repo/member.py`
**Implementation:** `src/infra/postgre/repo/member.py`
**Model:** [Member](../models/member.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> Member \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[Member]` | |
| `create` | `(dto: MemberCreate) -> Member` | |
| `update` | `(dto: MemberUpdate) -> Member` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `get_by_user_in_server(server_id, user_id) -> Member | None`
Получает участника по ID сервера и пользователя.

### `list_for_server(server_id) -> Sequence[Member]`
Список всех участников сервера.

### `list_active_for_server(server_id, page, nickname_filter, page_size) -> Sequence[Member]`
Список активных участников сервера с пагинацией и фильтром по нику.

### `create(server_id, user_id, nickname, server_role_id) -> Member`
Создаёт нового участника сервера.

При нарушении внешнего ключа (FK violation) выбрасывает `IntegrityForeignException`. При попытке создать дубликат пользователя на сервере выбрасывает `IntegrityUniqueException`.

### `set_role(member, server_role_id) -> Member`
Устанавливает роль участника. Если роль совпадает с текущей — операция пропускается.

### `set_nickname(member, nickname) -> Member`
Устанавливает ник участника. Если ник совпадает с текущим — операция пропускается.

### `set_user_if_none(member, user_id) -> bool`
Устанавливает user_id, если он ещё не установлен. Возвращает True, если user_id был установлен. Проверяет уникальность user_id на сервере — если пользователь уже является участником сервера, возвращает False.

### `remove_user(member) -> Member`
Удаляет user_id у участника (превращает в виртуального). Если user_id уже None — операция пропускается.

### `deactivate(member) -> Member`
Деактивирует участника. Если уже неактивен — операция пропускается.

### `activate(member) -> Member`
Активирует участника. Если уже активен — операция пропускается.
