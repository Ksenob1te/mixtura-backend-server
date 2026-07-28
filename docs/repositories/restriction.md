# RestrictionRepository

**Protocol:** `src/core/interfaces/repo/restriction.py`
**Implementation:** `src/infra/postgre/repo/restriction.py`
**Model:** [Restriction](../models/restriction.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(code_id: UUID) -> Restriction \| None` | Параметр назван `code_id` в протоколе (соответствует `id` в базовом классе) |
| `delete` | `(code_id: UUID) -> bool` | |

Протокол также объявляет собственный `create` (см. Custom Methods).

## Custom Methods

### `create(code) -> Restriction`
Создаёт новое ограничение. Принимает строковый код, создаёт ORM-объект и возвращает готовую модель.
- При нарушении уникальности кода (`SQLSTATE 23505`) выбрасывает `IntegrityUniqueException("Restriction with this code already exists")`.
- При прочих `IntegrityError` выбрасывает `IntegrityUnknownException`.

### `list_all() -> Sequence[Restriction]`
Возвращает список всех ограничений в системе. Выполняет `SELECT * FROM restriction`.

### `get_by_code(code) -> Restriction | None`
Получает ограничение по строковому коду. Выполняет `SELECT … WHERE code = :code LIMIT 1`.
> Метод отсутствует в протоколе `RestrictionRepositoryProtocol`, но реализован в классе `RestrictionRepository`.

### `get_by_code_bulk(codes) -> Sequence[Restriction]`
Получает несколько ограничений по списку кодов. Выполняет `SELECT … WHERE code IN :codes`.
