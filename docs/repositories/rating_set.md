# RatingSetRepository

**Protocol:** `src/core/interfaces/repo/rating_set.py`
**Implementation:** `src/infra/postgre/repo/rating_set.py`
**Model:** [RatingSet](../models/rating-set.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> RatingSet \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[RatingSet]` | |
| `create` | `(dto: RatingSetCreate) -> RatingSet` | |
| `update` | `(dto: RatingSetUpdate) -> RatingSet` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `get_by_game_id`

```python
async def get_by_game_id(self, game_id: UUID) -> RatingSet | None
```

Получает набор рейтингов по ID игры-владельца (`game_id` уникален — один набор рейтингов на игру).

### `get_detail`

```python
async def get_detail(self, rating_set_id: UUID) -> RatingSetDetail | None
```

Получает набор рейтингов вместе с вложенным списком `ratings` (загружается `lazy="selectin"`).
