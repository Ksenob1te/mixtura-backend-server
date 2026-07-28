# Rating

- **Pydantic file:** `src/core/models/rating.py`
- **ORM file:** `src/infra/postgre/models/rating.py`
- **Repo protocol:** `RatingRepositoryProtocol`
- **Used by services:** `RatingService`

## Role
Представляет уровень рейтинга в наборе рейтингов. Определяет пороговое значение и иконку для каждого уровня.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `rating_set_id` | `UUID` | ID набора рейтингов |
| `threshold` | `int` | Пороговое значение рейтинга |
| `icon_id` | `UUID \| None` | ID иконки |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `rating_set` | `RatingSet` | Набор рейтингов |

## Create/Update Models

### Create — `RatingCreate` (`src/core/models/rating.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `rating_set_id` | `UUID` | Yes | — | |
| `threshold` | `int` | Yes | — | |
| `icon_id` | `UUID \| None` | No | `None` | |

### Update — `RatingUpdate` (`src/core/models/rating.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `threshold` | `int \| None` | No | `None` | |
| `icon_id` | `UUID \| None` | No | `None` | |

> Поля `id`, `rating_set_id` неизменяемы после создания.

### Read — `Rating` (`src/core/models/rating.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `rating_set_id` | `UUID` | |
| `threshold` | `int` | |
| `icon_id` | `UUID \| None` | |
