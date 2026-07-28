# CustomRating

- **Pydantic file:** `src/core/models/custom_rating.py`
- **ORM file:** `src/infra/postgre/models/custom_rating.py`
- **Repo protocol:** `CustomRatingRepositoryProtocol`
- **Used by services:** `MemberCustomService`

## Role
Представляет оценку игровой роли в кастомном списке. Уникальна для пары `(custom_id, game_role_id)`.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `custom_id` | `UUID` | ID кастомного списка |
| `game_role_id` | `UUID` | ID игровой роли |
| `rating` | `int` | Оценка |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `custom` | `Custom` | Кастомный список |
| `game_role` | `GameRole` | Игровая роль |

## Create/Update Models

### Create — `CustomRatingCreate` (`src/core/models/custom_rating.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `custom_id` | `UUID` | Yes | — | |
| `game_role_id` | `UUID` | Yes | — | |
| `rating` | `int` | Yes | — | |

### Update — `CustomRatingUpdate` (`src/core/models/custom_rating.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `rating` | `int \| None` | No | `None` | |

> Поля `id`, `custom_id`, `game_role_id` неизменяемы после создания.

### Read — `CustomRating` (`src/core/models/custom_rating.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `custom_id` | `UUID` | |
| `game_role_id` | `UUID` | |
| `rating` | `int` | |
