# RatingRepository

**Protocol:** `src/core/interfaces/repo/rating.py`
**Implementation:** `src/infra/postgre/repo/rating.py`
**Model:** [Rating](../models/rating.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> Rating \| None` | |
| `get_list` | `(offset, limit, options, *where) -> Sequence[Rating]` | |
| `create` | `(dto: RatingCreate) -> Rating` | |
| `update` | `(dto: RatingUpdate) -> Rating` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `list_for_set(rating_set_id) -> Sequence[Rating]`
Список рейтингов для указанного набора рейтингов.

### `create(icon_id, threshold, rating_set_id) -> Rating`
Создаёт новый уровень рейтинга. Проверяет FK-ограничение: если rating_set_id не существует — `IntegrityForeignException`.

### `set_icon(rating, icon_id) -> Rating`
Устанавливает иконку уровня рейтинга.

### `set_threshold(rating, threshold) -> Rating`
Устанавливает пороговое значение рейтинга.

### `copy_rating(rating, new_rating_set_id) -> Rating`
Копирует уровень рейтинга в другой набор.

`copy_rating` — единственный кастомный метод, объявленный и в протоколе, и в реализации; используется `GameService.copy_global_game()` при копировании глобальной игры в воркспейс.
