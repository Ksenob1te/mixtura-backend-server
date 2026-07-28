# Permission Bits

**File:** `src/infra/postgre/static/permissions.py`

Битовая маска прав доступа. Права хранятся как `int` битовая маска в модели `Member.permission_mask` и передаются в запросах через `AccessDataRequest.permission_mask`.

## PERMISSION StrEnum

24+ кода прав, разделённые на категории. Каждому праву соответствует бит на позиции `pos`.

### ADMINISTRATOR

| Value | Position | Description |
|-------|----------|-------------|
| `ADMINISTRATOR` | 0 | Перезаписывает любую проверку — все права |

### Base Permissions

| Value | Position | Description |
|-------|----------|-------------|
| `EDIT_NAME` | 1 | Редактирование собственного имени |
| `EDIT_ROLES` | 2 | Назначение ролей участникам |
| `CREATE_VIRTUAL` | 3 | Создание виртуальных участников |
| `MIGRATE_MEMBERS` | 4 | Миграция участников между серверами |
| `KICK_MEMBERS` | 5 | Исключение участников |
| `CREATE_CUSTOM` | 6 | Создание кастомных списков |
| `DELETE_CUSTOM` | 7 | Удаление кастомных списков |
| `EDIT_ALL_CUSTOMS` | 8 | Редактирование любых кастомных списков |
| `EDIT_SERVER_ROLES` | 9 | Редактирование ролей сервера |

### Server Settings

| Value | Position | Description |
|-------|----------|-------------|
| `EDIT_SERVER_PUBLIC` | 10 | Изменение публичности сервера |
| `EDIT_SERVER_NAME` | 11 | Изменение названия сервера |
| `EDIT_SERVER_DESCRIPTION` | 12 | Изменение описания сервера |
| `EDIT_SERVER_BANNER` | 13 | Изменение баннера сервера |
| `EDIT_SERVER_ICON` | 14 | Изменение иконки сервера |
| `EDIT_SERVER_GAME` | 15 | Изменение игры сервера |
| `DELETE_SERVER` | 16 | Удаление сервера |
| `EDIT_ROLE_SET` | 17 | Изменение набора ролей |
| `EDIT_RATING_SET` | 18 | Изменение набора рейтингов |
| `EDIT_INVITES` | 19 | Управление приглашениями |

### Restriction Permissions

| Value | Position | Description |
|-------|----------|-------------|
| `RESTRICT_SERVER_BAN` | 20 | Наложение бана сервера |
| `RESTRICT_MIX_BAN` | 21 | Наложение бана микса |
| `RESTRICT_TOURNAMENT_BAN` | 22 | Наложение бана турнира |
| `RESTRICT_SELF_EDIT_NAME` | 23 | Запрет на смену имени |

### Event Permissions

| Value | Position | Description |
|-------|----------|-------------|
| `EVENT_CREATE` | 24 | Создание событий |
| `EVENT_ADMIN_VIEW` | 25 | Просмотр административных данных события |
| `EVENT_ADMIN_UPDATE` | 26 | Обновление события |
| `EVENT_ADMIN_MANAGE_ORGANIZERS` | 27 | Управление организаторами события |
| `EVENT_ADMIN_MANAGE_PLAYERS` | 28 | Управление игроками события |
| `EVENT_ADMIN_MANAGE_BRACKET` | 29 | Управление сеткой события |
| `EVENT_ADMIN_CANCEL` | 30 | Отмена события |
| `EVENT_ADMIN_COMPLETE` | 31 | Завершение события |

## Helper Functions

### `serialize_permission_codes(permissions: Iterable[PERMISSION]) -> int`

Преобразует набор прав в битовую маску.

### `deserialize_permission_codes(mask: int) -> set[PERMISSION]`

Преобразует битовую маску в набор прав.

### `check_permission(mask: int, permission: PERMISSION | str) -> bool`

Проверяет, установлено ли конкретное право в маске.

### `check_permission_bulk(mask: int, permissions: Iterable[PERMISSION], method: Callable) -> bool`

Проверяет набор прав с использованием заданной стратегии (`all()`, `any()` и т.д.).

## Usage Pattern

Проверка прав выполняется в сервисах через `PERMISSION.check_permission(mask, PERMISSION.CODE)`:

```python
if not PERMISSION.check_permission(member.permission_mask, PERMISSION.EDIT_NAME):
    raise ForbiddenException("Insufficient permissions")
```

`ADMINISTRATOR` (position 0) перезаписывает любую проверку — участник с этим правом имеет все разрешения.
