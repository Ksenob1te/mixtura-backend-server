# Restriction

- **Pydantic file:** `src/core/models/restriction.py`
- **ORM file:** `src/infra/postgre/models/restriction.py`
- **Repo protocol:** `RestrictionRepositoryProtocol`
- **Used by services:** `CoreService`, `AccessControlService`

## Role
Представляет тип ограничения в системе. Статические записи, создаваемые при инициализации из `RESTRICTION` StrEnum (см. [_shared/enums.md](../_shared/enums.md)).

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `code` | `str` | Код ограничения (`String(128)`, `unique=True`) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `member_restrictions` | `list[MemberRestriction]` | Ограничения участников этого типа |

## Create/Update Models

### Create — `RestrictionCreate` (`src/core/models/restriction.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `code` | `str` | Yes | — | Код ограничения |

> Ограничения не имеют Update-модели. Поля `id` и `code` неизменяемы после создания.

### Read — `Restriction` (`src/core/models/restriction.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `code` | `str` | |
