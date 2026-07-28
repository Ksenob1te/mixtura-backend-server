# ServerRoleRepository

**Protocol:** `src/core/interfaces/repo/server_role.py`
**Implementation:** `src/infra/postgre/repo/server_role.py`
**Model:** [ServerRole](../models/server-role.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> ServerRole \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[ServerRole]` | |
| `create` | `(dto: ServerRoleCreate) -> ServerRole` | |
| `update` | `(dto: ServerRoleUpdate) -> ServerRole` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `list_for_server(server_id) -> Sequence[ServerRole]`
Список ролей сервера, отсортированных по позиции (ASC).

### `create(server_id, name, position) -> ServerRole`
Создаёт роль на сервере. Сдвигает позиции существующих ролей (position >= new_position → position + 1). Проверяет уникальность имени в рамках сервера.

### `set_name(role, name) -> ServerRole`
Устанавливает название роли.

### `set_position(role, new_position) -> ServerRole`
Устанавливает позицию роли. Переиндексирует позиции других ролей сервера для сохранения порядка.
