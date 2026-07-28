# Member

- **Pydantic file:** `src/core/models/member.py`
- **ORM file:** `src/infra/postgre/models/member.py`
- **Repo protocol:** `MemberRepositoryProtocol`
- **Used by services:** `MemberService`, `AccessControlService`, `InviteService`, `MemberCustomService`

## Role
Представляет участника сервера. Связывает пользователя (user_id) с сервером, содержит права доступа и ограничения.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Уникальный идентификатор |
| `server_id` | `UUID` | ID сервера |
| `user_id` | `UUID \| None` | ID пользователя (None для виртуальных участников) |
| `nickname` | `str` | Отображаемое имя на сервере |
| `server_role_id` | `UUID \| None` | ID роли на сервере |
| `active` | `bool` | Флаг активности |
| `joined_at` | `datetime` | Дата присоединения |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `server` | `Server` | Сервер участника |
| `server_role` | `ServerRole \| None` | Роль участника |
| `permission_mask` | `int` | Битовая маска прав (поле ORM) |
| `restriction_mask` | `int` | Битовая маска ограничений (поле ORM) |

## Create/Update Models

### Create — `MemberCreate` (`src/core/models/member.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `server_id` | `UUID` | Yes | — | |
| `user_id` | `UUID \| None` | Yes | — | |
| `nickname` | `str` | Yes | — | |
| `server_role_id` | `UUID \| None` | No | `None` | |

### Update — `MemberUpdate` (`src/core/models/member.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `nickname` | `str \| None` | No | `None` | |
| `server_role_id` | `UUID \| None` | No | `None` | |

> Поля `id`, `server_id`, `user_id`, `active`, `joined_at` неизменяемы после создания.

### Read — `Member` (`src/core/models/member.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `server_id` | `UUID` | |
| `user_id` | `UUID \| None` | |
| `nickname` | `str` | |
| `server_role_id` | `UUID \| None` | |
| `active` | `bool` | |
| `joined_at` | `datetime` | |
