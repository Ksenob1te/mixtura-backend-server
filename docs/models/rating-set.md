# RatingSet

- **Pydantic file:** `src/core/models/rating_set.py`
- **ORM file:** `src/infra/postgre/models/rating_set.py`
- **Repo protocol:** `RatingSetRepositoryProtocol`
- **Used by services:** `GameService`, `RatingService`, `MemberCustomService`

## Role
Набор рейтинговых уровней, принадлежащий ровно одной игре (`Game`). Игра владеет своим набором рейтингов 1:1 — набор создаётся вместе с игрой и каскадно удаляется вместе с ней.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название набора |
| `min_rating` | `int` | Минимальный рейтинг |
| `max_rating` | `int` | Максимальный рейтинг |
| `game_id` | `UUID` | ID игры-владельца (уникально — один набор рейтингов на игру) |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `game` | `Game` | Игра-владелец набора |
| `ratings` | `list[Rating]` | Уровни рейтинга |

## Create/Update Models

### Create — `RatingSetCreate` (`src/core/models/rating_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `min_rating` | `int` | Yes | — | |
| `max_rating` | `int` | Yes | — | |
| `game_id` | `UUID` | Yes | — | |

### Update — `RatingSetUpdate` (`src/core/models/rating_set.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `min_rating` | `int \| None` | No | `None` | |
| `max_rating` | `int \| None` | No | `None` | |

> Поля `id` и `game_id` неизменяемы после создания.

### Read — `RatingSet` (`src/core/models/rating_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `min_rating` | `int` | |
| `max_rating` | `int` | |
| `game_id` | `UUID` | |

#### `RatingSetDetail` (`src/core/models/rating_set.py`)

| Field | Type | Notes |
|-------|------|-------|
| *(поля `RatingSet`)* | | |
| `ratings` | `list[Rating]` | Навигационное свойство |
