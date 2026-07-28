# Server

- **Pydantic file:** `src/core/models/server.py`
- **ORM file:** `src/infra/postgre/models/server.py`
- **Repo protocol:** `ServerRepositoryProtocol`
- **Used by services:** `CoreService`, `MemberService`, `InviteService`, `AccessControlService`, `RoleService`, `GameService`, `RatingService`, `GameRoleService`, `MemberCustomService`

## Role
Центральная модель системы. Представляет игровой сервер — контейнер для участников, игр, ролей, рейтингов и приглашений.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название сервера |
| `owner_id` | `UUID` | ID владельца сервера |
| `description` | `str` | Описание сервера |
| `public` | `bool` | Флаг публичности |
| `icon_id` | `UUID \| None` | ID иконки сервера |
| `banner_id` | `UUID \| None` | ID баннера сервера |
| `created_at` | `datetime` | Дата создания |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `role_set` | `GameRoleSet \| None` | Набор ролей сервера (1:1) |
| `rating_set` | `RatingSet \| None` | Набор рейтингов сервера (1:1) |
| `members` | `list[Member]` | Участники сервера |
| `server_games` | `list[ServerGame]` | Связи с играми через junction |
| `server_roles` | `list[ServerRole]` | Роли сервера |
| `invites` | `list[Invite]` | Приглашения сервера |
| `games` | `list[Game]` | Игры сервера (many-to-many через ServerGame) |

## Create/Update Models

### Create — `ServerCreate` (`src/core/models/server.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `owner_id` | `UUID` | Yes | — | |
| `description` | `str` | Yes | — | |
| `public` | `bool` | Yes | — | |

### Update — `ServerUpdate` (`src/core/models/server.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `description` | `str \| None` | No | `None` | |
| `public` | `bool \| None` | No | `None` | |
| `icon_id` | `UUID \| None` | No | `None` | |
| `banner_id` | `UUID \| None` | No | `None` | |

> Поля `id`, `owner_id`, `created_at` неизменяемы после создания.

### Read — `Server` (`src/core/models/server.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `owner_id` | `UUID` | |
| `description` | `str` | |
| `public` | `bool` | |
| `icon_id` | `UUID \| None` | |
| `banner_id` | `UUID \| None` | |
| `created_at` | `datetime` | |
