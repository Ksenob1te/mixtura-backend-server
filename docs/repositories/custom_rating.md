# CustomRatingRepository

**Protocol:** `src/core/interfaces/repo/custom_rating.py`
**Implementation:** `src/infra/postgre/repo/custom_rating.py`
**Model:** [CustomRating](../models/custom-rating.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> CustomRating \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[CustomRating]` | |
| `create` | `(dto: CustomRatingCreate) -> CustomRating` | |
| `update` | `(dto: CustomRatingUpdate) -> CustomRating` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `get_by_custom_role(custom_id, game_role_id) -> CustomRating | None`
Получает оценку по кастомному списку и игровой роли.

### `list_for_custom(custom_id) -> Sequence[CustomRating]`
Список всех оценок в кастомном списке.

### `create(custom_id, game_role_id, rating) -> CustomRating`
Создаёт оценку. Проверяет уникальность пары (custom_id, game_role_id) и FK-ограничения.

### `set_rating(custom_rating, rating) -> CustomRating`
Устанавливает значение оценки.

### `delete_by_custom_rating(custom_id, game_role_id) -> bool`
Удаляет оценку по кастомному списку и игровой роли. Возвращает True, если удаление произошло.
