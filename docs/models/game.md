# Game

- **Pydantic file:** `src/core/models/game.py`
- **ORM file:** `src/infra/postgre/models/game.py`
- **Repo protocol:** `GameRepositoryProtocol`
- **Used by services:** `GameService`, `GameRoleService`, `RatingService`, `MemberCustomService`

## Role
Представляет игру — глобальную (управляется сайт-админом через `game.global.*` очереди, `server_id = NULL`) или локальную (принадлежит одному серверу-воркспейсу, `server_id` указан). Каждая игра владеет ровно одним набором ролей (`role_set`) и одним набором рейтингов (`rating_set`); оба каскадно удаляются вместе с игрой.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название игры. Уникально в рамках сервера (`uq_game_server_name`); для глобальных игр (`server_id IS NULL`) — уникально среди всех глобальных (частичный индекс `uq_game_global_name`) |
| `server_id` | `UUID \| None` | ID сервера-владельца. `None` — глобальная игра |
| `icon_id` | `UUID \| None` | ID иконки |
| `banner_id` | `UUID \| None` | ID баннера |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server \| None` | Сервер-владелец локальной игры (`None` для глобальной) |
| `role_set` | `GameRoleSet` | Набор ролей игры (1:1, `cascade="all, delete-orphan"`) |
| `rating_set` | `RatingSet` | Набор рейтингов игры (1:1, `cascade="all, delete-orphan"`) |
| `server_games` | `list[ServerGame]` | Связи с серверами, подключившими игру, через junction |
| `servers` | `list[Server]` | Серверы, подключившие игру (many-to-many через `ServerGame`, `viewonly=True`) |

## Create/Update Models

### Create — `GameCreate` (`src/core/models/game.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `server_id` | `UUID \| None` | No | `None` | `None` создаёт глобальную игру |
| `icon_id` | `UUID \| None` | No | `None` | |
| `banner_id` | `UUID \| None` | No | `None` | |

### Update — `GameUpdate` (`src/core/models/game.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `icon_id` | `UUID \| None` | No | `None` | |
| `banner_id` | `UUID \| None` | No | `None` | |

> Поля `id` и `server_id` неизменяемы после создания — игру нельзя перенести между глобальной и локальной областью или между серверами.

### Read — `Game` (`src/core/models/game.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `server_id` | `UUID \| None` | |
| `icon_id` | `UUID \| None` | |
| `banner_id` | `UUID \| None` | |
| `is_global` | `bool` | Вычисляемое свойство (`server_id is None`); не поле — отсутствует в `model_dump()`, недоступно для записи клиентом |

#### `GameDetail` (`src/core/models/game.py`)

Расширяет `Game` вложенными наборами. Это форма, которую возвращают все очереди `game.*`.

| Field | Type | Notes |
|-------|------|-------|
| *(поля `Game`)* | | |
| `role_set` | `GameRoleSetDetail` | Навигационное свойство — набор ролей с вложенным списком `game_roles` |
| `rating_set` | `RatingSetDetail` | Навигационное свойство — набор рейтингов с вложенным списком `ratings` |
