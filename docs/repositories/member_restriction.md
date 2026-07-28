# MemberRestrictionRepository

**Protocol:** `src/core/interfaces/repo/member_restriction.py`
**Implementation:** `src/infra/postgre/repo/member_restriction.py`
**Model:** [MemberRestriction](../models/member-restriction.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(restriction_id: UUID) -> MemberRestriction \| None` | |
| `delete` | `(restriction_id: UUID) -> bool` | |

## Custom Methods

### `list_for_member(member_id: UUID) -> Sequence[MemberRestriction]`
Список всех ограничений указанного участника. Фильтрация по `member_id`.

### `list_active_for_member(member_id: UUID, now: datetime | None = None) -> Sequence[MemberRestriction]`
Список активных (не истёкших) ограничений участника. Если `now` не передан, используется `datetime.now(timezone.utc)`. Фильтр: `expiration_date > now`.

### `create(member_id: UUID, restriction_id: UUID, reason: str, expiration_date: datetime, creator_id: UUID) -> MemberRestriction`
Создаёт запись `MemberRestriction` в БД. Обрабатывает `IntegrityError`:

| Условие | Исключение |
|---------|------------|
| Нарушение внешнего ключа (`SQLSTATE 23503`) — member, restriction или creator не найдены | `IntegrityForeignException` |
| Любая другая ошибка целостности | `IntegrityUnknownException` |

Возвращает свежесозданную запись через `get(r.id)`. Если после flush запись не найдена — `IntegrityUnknownException`.

### `set_reason(restriction: MemberRestriction, reason: str) -> MemberRestriction`
Обновляет причину ограничения напрямую через мутацию ORM-объекта + `flush`.

### `set_expiration(restriction: MemberRestriction, expiration_date: datetime) -> MemberRestriction`
Обновляет дату истечения ограничения напрямую через мутацию ORM-объекта + `flush`.

### `set_code(restriction: MemberRestriction, restriction_code_id: UUID) -> MemberRestriction`
Обновляет код ограничения (`restriction_id`) напрямую через мутацию ORM-объекта + `flush`.
