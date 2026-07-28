# Game

- **Pydantic file:** `src/core/models/game.py`
- **ORM file:** `src/infra/postgre/models/game.py`
- **Repo protocol:** `GameRepositoryProtocol`
- **Used by services:** `CoreService`, `GameService`

## Role
Представляет игру, которая может быть добавлена на сервер. Глобальный справочник игр.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `name` | `str` | Название игры |
| `icon_id` | `UUID` | ID иконки |
| `banner_id` | `UUID` | ID баннера |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `servers` | `list[Server]` | Серверы, на которых добавлена игра (many-to-many через ServerGame) |

## Create/Update Models

### Create — `GameCreate` (`src/core/models/game.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str` | Yes | — | |
| `icon_id` | `UUID` | Yes | — | |
| `banner_id` | `UUID` | Yes | — | |

### Update — `GameUpdate` (`src/core/models/game.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `str \| None` | No | `None` | |
| `icon_id` | `UUID \| None` | No | `None` | |
| `banner_id` | `UUID \| None` | No | `None` | |

> Поле `id` неизменяемо после создания.

### Read — `Game` (`src/core/models/game.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `name` | `str` | |
| `icon_id` | `UUID` | |
| `banner_id` | `UUID` | |
