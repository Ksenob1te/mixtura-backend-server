# Core — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/core.py`
- **Service file:** `src/core/services/core.py`
- **Commands file:** `src/core/commands/server.py`
- **Results file:** `src/core/results/server.py`
- **Request models:** `src/app/rabbit/models/server.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `server.public_server_list` | `GetPublicServersRequest` | `list[ServerListResponse]` | Список публичных серверов |
| `server.user_server_list` | `GetUserServersRequest` | `list[ServerListResponse]` | Список серверов пользователя |
| `server.create` | `ServerCreateRequest` | `ServerDetailResponse` | Создание сервера |
| `server.get_info` | `ServerGetRequest` | `ServerDetailResponse` | Получение информации о сервере |
| `server.update` | `ServerUpdateRequest` | `ServerDetailResponse` | Обновление сервера |
| `server.banner.delete` | `ServerDeleteRequest` | `StatusResponse` | Удаление баннера |
| `server.icon.delete` | `ServerDeleteRequest` | `StatusResponse` | Удаление иконки |
| `server.delete` | `ServerDeleteRequest` | `StatusResponse` | Удаление сервера |

---

## Queue: `server.public_server_list`

### Command: `GetPublicServersRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pagination` | `PaginationRequest` | Yes | Пагинация |
| `name_filter` | `str` | No | Фильтр по названию |

### Result: `list[ServerListResponse]`
→ См. [_shared/response-wrapper.md](../../_shared/response-wrapper.md) для конверта.

**ServerListResponse:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | |
| `name` | `str` | |
| `description` | `str` | |
| `icon_id` | `UUID \| None` | |
| `banner_id` | `UUID \| None` | |
| `owner_id` | `UUID` | |
| `public` | `bool` | |
| `created_at` | `datetime` | |

---

## Queue: `server.user_server_list`

### Command: `GetUserServersRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `UUID` | Yes | ID пользователя |
| `pagination` | `PaginationRequest` | Yes | Пагинация |
| `name_filter` | `str` | No | Фильтр по названию |

### Result: `list[ServerListResponse]`
→ Как в `server.public_server_list`.

---

## Queue: `server.create`

### Command: `ServerCreateRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `UUID` | Yes | ID создателя |
| `user_name` | `str` | Yes | Имя создателя |
| `name` | `str` | Yes | Название сервера (max 128) |
| `description` | `str` | No | Описание |
| `public` | `bool` | Yes | Публичность |
| `rating_set_id` | `UUID \| None` | No | Шаблон рейтинга |
| `role_set_id` | `UUID \| None` | No | Шаблон ролей |

### Result: `ServerDetailResponse`
| Field | Type | Description |
|-------|------|-------------|
| *(поля ServerListResponse)* | | |
| `rating_set` | `RatingSetResponse \| None` | Набор рейтингов |
| `role_set` | `GameRoleSetResponse \| None` | Набор ролей |
| `games` | `list[GameResponse]` | Игры сервера |

### Behavior
- Если role_set_id указан — копирует глобальный шаблон ролей на сервер
- Если rating_set_id указан — копирует глобальный шаблон рейтингов на сервер
- Автоматически создаёт владельца как первого участника

---

## Queue: `server.get_info`

### Command: `ServerGetRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |

### Result: `ServerDetailResponse`
→ Как в `server.create`.

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |

---

## Queue: `server.update`

### Command: `ServerUpdateRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |
| `name` | `str \| None` | No | Название (max 128) |
| `description` | `str \| None` | No | Описание |
| `public` | `bool \| None` | No | Публичность |
| `banner_id` | `UUID \| None` | No | ID баннера |
| `icon_id` | `UUID \| None` | No | ID иконки |

### Result: `ServerDetailResponse`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |

---

## Queue: `server.banner.delete`

### Command: `ServerDeleteRequest`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | Блок авторизации |

### Result: `StatusResponse`
→ `{ "status": "ok" }`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |

---

## Queue: `server.icon.delete`

### Command: `ServerDeleteRequest`
→ Как в `server.banner.delete`.

### Result: `StatusResponse`

### Exceptions
→ Как в `server.banner.delete`.

---

## Queue: `server.delete`

### Command: `ServerDeleteRequest`
→ Как в `server.banner.delete`.

### Result: `StatusResponse`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден |
| `ForbiddenException` | Недостаточно прав |
| `InternalLogicException` | Ошибка удаления |
