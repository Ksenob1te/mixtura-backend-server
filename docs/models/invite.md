# Invite

- **Pydantic file:** `src/core/models/invite.py`
- **ORM file:** `src/infra/postgre/models/invite.py`
- **Repo protocol:** `InviteRepositoryProtocol`
- **Used by services:** `InviteService`

## Role
Представляет приглашение на сервер. Содержит ключ для входа и лимит использований.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `server_id` | `UUID` | ID сервера |
| `inviter_id` | `UUID \| None` | ID пригласившего участника |
| `key` | `str` | Ключ приглашения |
| `use_limit` | `int` | Лимит использований |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server` | Сервер приглашения |
| `inviter` | `Member \| None` | Пригласивший участник |

## Create/Update Models

### Create — `InviteCreate` (`src/core/models/invite.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `server_id` | `UUID` | Yes | — | |
| `use_limit` | `int` | Yes | — | |
| `inviter_id` | `UUID \| None` | No | `None` | |
| `key` | `str \| None` | No | `None` | Авто-генерация если не указан |

### Update — `InviteUpdate` (`src/core/models/invite.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `use_limit` | `int \| None` | No | `None` | |

> Поля `id`, `server_id`, `inviter_id`, `key` неизменяемы после создания.

### Read — `Invite` (`src/core/models/invite.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `server_id` | `UUID` | |
| `inviter_id` | `UUID \| None` | |
| `key` | `str` | |
| `use_limit` | `int` | |
