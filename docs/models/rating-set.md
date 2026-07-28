# RatingSet

- **Pydantic file:** `src/core/models/rating_set.py`
- **ORM file:** `src/infra/postgre/models/rating_set.py`
- **Repo protocol:** `RatingSetRepositoryProtocol`
- **Used by services:** `CoreService`, `RatingService`

## Role
Представляет набор рейтинговых уровней. Может быть глобальным шаблоном или принадлежать конкретному серверу.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название набора |
| `min_rating` | `int` | Минимальный рейтинг |
| `max_rating` | `int` | Максимальный рейтинг |
| `is_global` | `bool` | Флаг глобального шаблона |
| `server_id` | `UUID \| None` | ID сервера (если не глобальный) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server \| None` | Сервер набора |
| `ratings` | `list[Rating]` | Уровни рейтинга |

## Create/Update Models

### Create — `RatingSetCreate` (`src/core/models/rating_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `min_rating` | `int` | Yes | — | |
| `max_rating` | `int` | Yes | — | |
| `is_global` | `bool` | No | `False` | |
| `server_id` | `UUID \| None` | No | `None` | |

### Update — `RatingSetUpdate` (`src/core/models/rating_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `min_rating` | `int \| None` | No | `None` | |
| `max_rating` | `int \| None` | No | `None` | |

> Поля `id`, `is_global`, `server_id` неизменяемы после создания.

### Read — `RatingSet` (`src/core/models/rating_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `min_rating` | `int` | |
| `max_rating` | `int` | |
| `is_global` | `bool` | |
| `server_id` | `UUID \| None` | |
