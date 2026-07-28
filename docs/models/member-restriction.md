# MemberRestriction

- **Pydantic file:** `src/core/models/member_restriction.py`
- **ORM file:** `src/infra/postgre/models/member_restriction.py`
- **Repo protocol:** `MemberRestrictionRepositoryProtocol` (`src/core/interfaces/repo/member_restriction.py`)
- **Used by services:** `AccessControlService`

## Role
Представляет ограничение, наложенное на участника сервера. Содержит тип ограничения, причину и срок действия. Связывает участника (`Member`) с типом ограничения (`Restriction`).

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `member_id` | `UUID` | ID участника, на которого наложено ограничение |
| `restriction_id` | `UUID` | ID типа ограничения |
| `reason` | `str` | Причина ограничения |
| `expiration_date` | `datetime` (timezone-aware) | Дата истечения срока действия ограничения |
| `creator_id` | `UUID \| None` | ID создателя (кто наложил); `None` если создатель удалён |

> `creator_id` может быть `None` на уровне ORM (Foreign Key `SET NULL` при удалении создателя), однако в Pydantic-модели поле обязательно. Это означает, что при создании ограничения creator_id всегда указывается.

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `member` | `Member` | Участник, на которого наложено ограничение (`back_populates='restrictions'`) |
| `restriction` | `Restriction` | Тип ограничения (`back_populates='member_restrictions'`) |
| `creator` | `Member` | Создатель ограничения (участник, наложивший ограничение) |

### ORM Mapping

- **Таблица:** `member_restriction_table`
- **`member_id`:** `ForeignKey('member_table.id', ondelete='CASCADE')` — при удалении участника его ограничения удаляются
- **`restriction_id`:** `ForeignKey('restriction_table.id', ondelete='RESTRICT')` — запрещено удалять тип ограничения, пока есть активные ограничения
- **`creator_id`:** `ForeignKey('member_table.id', ondelete='SET NULL')` — при удалении создателя поле становится `None`
- Все связи загружаются лениво (`lazy="selectin"`)

## Create/Update Models

### Create — `MemberRestrictionCreate` (`src/core/models/member_restriction.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `member_id` | `UUID` | Yes | — | Участник, на которого накладывается ограничение |
| `restriction_id` | `UUID` | Yes | — | Тип ограничения |
| `reason` | `str` | Yes | — | Причина |
| `expiration_date` | `datetime` | Yes | — | Дата истечения (timezone-aware) |
| `creator_id` | `UUID` | Yes | — | Кто наложил ограничение |

> MemberRestriction не имеет Update-модели. Изменение ограничения не предусмотрено — существующее ограничение удаляется, при необходимости создаётся новое.

### Read — `MemberRestriction` (`src/core/models/member_restriction.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `member_id` | `UUID` | |
| `restriction_id` | `UUID` | |
| `reason` | `str` | |
| `expiration_date` | `datetime` | |
| `creator_id` | `UUID` | |

## Repository Methods

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `get` | `restriction_id: UUID` | `MemberRestriction \| None` | Получить ограничение по ID |
| `list_for_member` | `member_id: UUID` | `Sequence[MemberRestriction]` | Список всех ограничений участника |
| `create` | `member_id, restriction_id, reason, expiration_date, creator_id` | `MemberRestriction` | Создать новое ограничение |
| `delete` | `restriction_id: UUID` | `bool` | Удалить ограничение |
