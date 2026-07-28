# RatingSetRepository

**Protocol:** `src/core/interfaces/repo/rating_set.py`
**Implementation:** `src/infra/postgre/repo/rating_set.py`
**Model:** [RatingSet](../models/rating-set.md)

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> RatingSet \| None` | |
| `delete` | `(field_id: UUID) -> bool` | |

## Custom Methods

### `get_by_name(name) -> RatingSet | None`

```python
async def get_by_name(self, name: str) -> RatingSet | None
```

Получает набор рейтингов по названию. Возвращает `None`, если набор с таким именем не найден.

### `get_global() -> Sequence[RatingSet]`

```python
async def get_global(self) -> Sequence[RatingSet]
```

Список всех глобальных наборов рейтингов (шаблонов). Фильтрует записи по флагу `is_global == True`.

### `create(name, min_rating, max_rating, is_global, server_id) -> RatingSet`

```python
async def create(self, name: str, min_rating: int, max_rating: int, is_global: bool = False,
                 server_id: UUID | None = None) -> RatingSet
```

Создаёт новый набор рейтингов. Если `min_rating > max_rating` — `min_rating` приравнивается к `max_rating`. После flush повторно загружает созданную запись через `get`. При нарушении целостности выбрасывает `IntegrityUnknownException`.

### `set_name(rating_set, name) -> RatingSet`

```python
async def set_name(self, rating_set: RatingSet, name: str) -> RatingSet
```

Устанавливает название набора рейтингов.

### `set_min_rating(rating_set, min_rating) -> RatingSet`

```python
async def set_min_rating(self, rating_set: RatingSet, min_rating: int) -> RatingSet
```

Устанавливает минимальный рейтинг. Если `min_rating` превышает текущий `max_rating`, значение приравнивается к `max_rating`.

### `set_max_rating(rating_set, max_rating) -> RatingSet`

```python
async def set_max_rating(self, rating_set: RatingSet, max_rating: int) -> RatingSet
```

Устанавливает максимальный рейтинг. Если `max_rating` меньше текущего `min_rating`, значение приравнивается к `min_rating`.

### `set_global(rating_set, is_global) -> RatingSet`

```python
async def set_global(self, rating_set: RatingSet, is_global: bool) -> RatingSet
```

Устанавливает флаг глобальности набора рейтингов.

### `copy_global(global_rating_set, server_id) -> RatingSet`

```python
async def copy_global(self, global_rating_set: RatingSet, server_id: UUID | None = None) -> RatingSet
```

Копирует глобальный шаблон набора рейтингов на сервер. Создаёт новый набор с теми же `name`, `min_rating`, `max_rating`, флагом `is_global=False` и привязкой к указанному `server_id`.
