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

### `get_by_game_id`

```python
async def get_by_game_id(self, game_id: UUID) -> GameRoleSet | None
```

Получает набор ролей по ID игры-владельца (`game_id` уникален — один набор ролей на игру).

### `get_detail`

```python
async def get_detail(self, role_set_id: UUID) -> GameRoleSetDetail | None
```

Получает набор ролей вместе с вложенным списком `game_roles` (загружается `lazy="selectin"`).
