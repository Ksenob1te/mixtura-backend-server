# Enums

Все enum-ы определены как `StrEnum` и сериализуются в строковые значения.

## PERMISSION

- **File:** `src/infra/postgre/static/permissions.py`
- **Используется:** Битовые маски прав участников
- **Подробно:** [_shared/permission-bits.md](permission-bits.md)

| Value | Description |
|-------|-------------|
| `ADMINISTRATOR` | Перезаписывает любую проверку — все права |
| `EDIT_NAME` | Редактирование имени |
| `EDIT_ROLES` | Назначение ролей |
| `CREATE_VIRTUAL` | Создание виртуальных участников |
| `MIGRATE_MEMBERS` | Миграция участников |
| `KICK_MEMBERS` | Исключение участников |
| `CREATE_CUSTOM` | Создание кастомных списков |
| `DELETE_CUSTOM` | Удаление кастомных списков |
| `EDIT_ALL_CUSTOMS` | Редактирование любых кастомных списков |
| `EDIT_SERVER_ROLES` | Редактирование ролей сервера |
| `EDIT_SERVER_PUBLIC` | Изменение публичности сервера |
| `EDIT_SERVER_NAME` | Изменение названия сервера |
| `EDIT_SERVER_DESCRIPTION` | Изменение описания сервера |
| `EDIT_SERVER_BANNER` | Изменение баннера сервера |
| `EDIT_SERVER_ICON` | Изменение иконки сервера |
| `EDIT_SERVER_GAME` | Изменение игры сервера |
| `DELETE_SERVER` | Удаление сервера |
| `EDIT_ROLE_SET` | Изменение набора ролей |
| `EDIT_RATING_SET` | Изменение набора рейтингов |
| `EDIT_INVITES` | Управление приглашениями |
| `RESTRICT_SERVER_BAN` | Наложение бана сервера |
| `RESTRICT_MIX_BAN` | Наложение бана микса |
| `RESTRICT_TOURNAMENT_BAN` | Наложение бана турнира |
| `RESTRICT_SELF_EDIT_NAME` | Запрет на смену имени |
| `EVENT_CREATE` | Создание событий |
| `EVENT_ADMIN_VIEW` | Просмотр админ-данных события |
| `EVENT_ADMIN_UPDATE` | Обновление события |
| `EVENT_ADMIN_MANAGE_ORGANIZERS` | Управление организаторами |
| `EVENT_ADMIN_MANAGE_PLAYERS` | Управление игроками |
| `EVENT_ADMIN_MANAGE_BRACKET` | Управление сеткой |
| `EVENT_ADMIN_CANCEL` | Отмена события |
| `EVENT_ADMIN_COMPLETE` | Завершение события |

## RESTRICTION

- **File:** `src/infra/postgre/static/restrictions.py`
- **Используется:** Битовые маски ограничений участников

| Value | Description |
|-------|-------------|
| `SERVER_BAN` | Бан на сервере |
| `MIX_BAN` | Бан в миксах |
| `TOURNAMENT_BAN` | Бан в турнирах |
| `SELF_EDIT_NAME` | Запрет на самостоятельное изменение имени |

### Helper Functions

- `serialize_restriction_codes(restrictions) -> int` — преобразует набор ограничений в битовую маску
- `deserialize_restriction_codes(mask) -> set` — преобразует маску в набор ограничений
- `check_restriction(mask, restriction) -> bool` — проверяет наличие ограничения

## RepositoryException

- **File:** `src/infra/postgre/exceptions.py`
- **Используется:** Слой репозиториев

| Value | Description |
|-------|-------------|
| `RepositoryException` | Базовое исключение репозитория |
| `IntegrityForeignException` | Нарушение внешнего ключа |
| `IntegrityUniqueException` | Нарушение уникальности |
| `IntegrityUnknownException` | Неизвестная ошибка целостности |
| `InviteUniqueException` | Дубликат приглашения |
