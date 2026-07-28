# GameRoleSetRepository

**Protocol:** `src/core/interfaces/repo/game_role_set.py`
**Implementation:** `src/infra/postgre/repo/game_role_set.py`
**Model:** [GameRoleSet](../models/game-role-set.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> GameRoleSet \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[GameRoleSet]` | |
| `create` | `(dto: GameRoleSetCreate) -> GameRoleSet` | |
| `update` | `(dto: GameRoleSetUpdate) -> GameRoleSet` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `get_by_name(name) -> GameRoleSet | None`
Получает набор ролей по названию.

### `get_global() -> Sequence[GameRoleSet]`
Список всех глобальных наборов ролей (шаблонов).

### `create(name, is_global, server_id) -> GameRoleSet`
Создаёт новый набор ролей.

### `set_name(role_set, name) -> GameRoleSet`
Устанавливает название набора ролей.

### `set_global(role_set, is_global) -> GameRoleSet`
Устанавливает флаг глобальности набора.

### `copy_global(global_role_set, server_id) -> GameRoleSet`
Копирует глобальный шаблон набора ролей на сервер с is_global=False.
