# Custom

- **Pydantic file:** `src/core/models/custom.py`
- **ORM file:** `src/infra/postgre/models/custom.py`
- **Repo protocol:** `CustomRepositoryProtocol`
- **Used by services:** `MemberCustomService`

## Role
Представляет кастомный список рейтингов участника. Содержит набор оценок для разных игровых ролей.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `member_id` | `UUID` | ID участника-владельца |
| `creator_id` | `UUID \| None` | ID создателя (если создан другим участником) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `member` | `Member` | Участник-владелец |
| `creator` | `Member \| None` | Создатель |
| `custom_ratings` | `list[CustomRating]` | Оценки в этом кастомном списке |

## Create/Update Models

### Create — `CustomCreate` (`src/core/models/custom.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `member_id` | `UUID` | Yes | — | ID участника-владельца |
| `creator_id` | `UUID \| None` | No | `None` | ID создателя |

> Custom не имеет Update-модели. Поле `id` неизменяемо после создания.

### Read — `Custom` (`src/core/models/custom.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `member_id` | `UUID` | |
| `creator_id` | `UUID \| None` | |
| `custom_ratings` | `list[CustomRating]` | Навигационное свойство |
