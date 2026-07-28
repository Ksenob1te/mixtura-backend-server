# Mixtura Server-Service — Documentation Index

> **INSTRUCTION FOR AGENTS:** При внесении изменений в код ОБЯЗАТЕЛЬНО обновляйте соответствующие файлы документации.
>
> **NOTE FOR AGENTS:** Структура и содержание файлов документации описаны в [guides/structure.md](guides/structure.md). Перед созданием нового файла или редактированием существующего — ознакомьтесь с ней.
>
> | Изменение в коде | Что обновить |
> |------------------|--------------|
> | Новый/изменённый handler/queue | `<feature>/api.md` — контракты |
> | Новый/изменённый метод сервиса | `<feature>/service.md` — алгоритм, исключения, зависимости |
> | Новая/изменённая команда/DTO запроса | `<feature>/api.md` — схема Command/Request |
> | Новый/изменённый результат/DTO ответа | `<feature>/api.md` или перенести в `_shared/<schema>.md` если переиспользуется |
> | Новая/изменённая модель | `models/<model>.md` — поля, роль, связи |
> | Изменение общих схем | `_shared/<file>.md` |
> | Новый/изменённый репозиторий/DAO | `repositories/<name>.md` — методы |
> | Новый модуль/сервис | Создать `<feature>/api.md` + `<feature>/service.md`, добавить в таблицу модулей |
> | Удаление кода | Удалить из соответствующих `.md` файлов |

## Modules

| Module | API Contracts | Service Logic |
|--------|--------------|---------------|
| Core | [api.md](modules/core/api.md) | [service.md](modules/core/service.md) |
| Member | [api.md](modules/member/api.md) | [service.md](modules/member/service.md) |
| Access Control | — | [service.md](modules/access-control/service.md) |
| Server Role | [api.md](modules/server-role/api.md) | [service.md](modules/server-role/service.md) |
| Rating | [api.md](modules/rating/api.md) | [service.md](modules/rating/service.md) |
| Game Role | [api.md](modules/game-role/api.md) | [service.md](modules/game-role/service.md) |
| Game | [api.md](modules/game/api.md) | [service.md](modules/game/service.md) |
| Invite | [api.md](modules/invite/api.md) | [service.md](modules/invite/service.md) |
| Custom | [api.md](modules/custom/api.md) | [service.md](modules/custom/service.md) |

## Shared Components

| Component | File | Description |
|-----------|------|-------------|
| Domain Exceptions | [_shared/domain-exceptions.md](_shared/domain-exceptions.md) | Иерархия исключений, коды и условия |
| Permission Bits | [_shared/permission-bits.md](_shared/permission-bits.md) | Битовые маски прав доступа |
| Enums | [_shared/enums.md](_shared/enums.md) | PERMISSION, RESTRICTION, RepositoryException |
| AccessDataRequest | [_shared/access-data.md](_shared/access-data.md) | Блок авторизации запросов |
| Pagination | [_shared/pagination.md](_shared/pagination.md) | Стандартная пагинация |
| Response Envelope | [_shared/response-wrapper.md](_shared/response-wrapper.md) | Generic конверт ответа |

## Domain Models

| Model | File | Description |
|-------|------|-------------|
| Server | [models/server.md](models/server.md) | Игровой сервер — центральная сущность |
| Member | [models/member.md](models/member.md) | Участник сервера |
| Game | [models/game.md](models/game.md) | Игра — глобальная (сайт-админ) или локальная (принадлежит серверу) |
| GameRole | [models/game-role.md](models/game-role.md) | Роль в наборе ролей |
| GameRoleSet | [models/game-role-set.md](models/game-role-set.md) | Набор ролей игры (1:1 с игрой) |
| Rating | [models/rating.md](models/rating.md) | Уровень рейтинга |
| RatingSet | [models/rating-set.md](models/rating-set.md) | Набор рейтингов игры (1:1 с игрой) |
| Invite | [models/invite.md](models/invite.md) | Приглашение на сервер |
| Permission | [models/permission.md](models/permission.md) | Право доступа |
| ServerRole | [models/server-role.md](models/server-role.md) | Роль сервера |
| Restriction | [models/restriction.md](models/restriction.md) | Тип ограничения |
| Custom | [models/custom.md](models/custom.md) | Кастомный список рейтингов |
| CustomRating | [models/custom-rating.md](models/custom-rating.md) | Оценка в кастомном списке |
| MemberRestriction | [models/member-restriction.md](models/member-restriction.md) | Ограничение участника |
| ServerGame | [models/server-game.md](models/server-game.md) | Связь сервера и игры (junction) |
| ServerRolePermission | [models/server-role-permission.md](models/server-role-permission.md) | Связь роли и права (junction) |

## Repositories

> **Note for agents:** Новые репозитории должны наследоваться от `BaseRepositoryImpl[Model]` **и** от соответствующего `*RepositoryProtocol`. Описывайте только кастомные методы — базовые CRUD методы уже задокументированы в [base.md](repositories/base.md).

| Repository | File | Description |
|------------|------|-------------|
| BaseRepository | [repositories/base.md](repositories/base.md) | Generic CRUD (get, delete) |
| ServerRepository | [repositories/server.md](repositories/server.md) | Серверы: CRUD, фильтрация |
| MemberRepository | [repositories/member.md](repositories/member.md) | Участники: CRUD, активация |
| GameRepository | [repositories/game.md](repositories/game.md) | Игры: CRUD, управление на сервере |
| GameRoleRepository | [repositories/game_role.md](repositories/game_role.md) | Игровые роли: CRUD, копирование |
| GameRoleSetRepository | [repositories/game_role_set.md](repositories/game_role_set.md) | Наборы ролей игр: CRUD |
| RatingRepository | [repositories/rating.md](repositories/rating.md) | Уровни рейтинга: CRUD, копирование |
| RatingSetRepository | [repositories/rating_set.md](repositories/rating_set.md) | Наборы рейтингов игр: CRUD |
| InviteRepository | [repositories/invite.md](repositories/invite.md) | Приглашения: ключи, лимиты |
| PermissionRepository | [repositories/permission.md](repositories/permission.md) | Права: CRUD, назначение ролям |
| ServerRoleRepository | [repositories/server_role.md](repositories/server_role.md) | Роли сервера: позиции, переиндексация |
| RestrictionRepository | [repositories/restriction.md](repositories/restriction.md) | Типы ограничений |
| CustomRepository | [repositories/custom.md](repositories/custom.md) | Кастомные списки |
| CustomRatingRepository | [repositories/custom_rating.md](repositories/custom_rating.md) | Оценки в кастомных списках |
| MemberRestrictionRepository | [repositories/member_restriction.md](repositories/member_restriction.md) | Ограничения участников |
