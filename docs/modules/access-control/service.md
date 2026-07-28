# AccessControlService — Business Logic

## Overview
- **File:** `src/core/services/access_control.py`
- **Private helpers:**
  - `_transform_permissions_to_enum(permissions: list[Permission]) -> list[PERMISSION]` — преобразует ORM Permission модели в доменные PERMISSION enum по коду
  - `_transform_enum_to_permissions(permissions: list[PERMISSION]) -> list[Permission]` — преобразует PERMISSION enum обратно в ORM Permission модели через bulk-запрос
  - `_transform_permission_to_mask(permissions: list[Permission]) -> int` — сериализует набор Permission в битовую маску
  - `_compute_overwrites_enum(permissions: list[PERMISSION], is_owner: bool) -> list[PERMISSION]` — расширяет права до полного набора если присутствует ADMINISTRATOR или участник — владелец
  - `_compute_overwrites_mask(permission_mask: int, is_owner: bool) -> int` — возвращает полную битовую маску если есть ADMINISTRATOR или владелец
  - `_can_manipulate_restrictions(issuer: Member, member: Member, server: Server) -> None` — проверяет может ли выдающий участник накладывать/снимать ограничения на целевого участника (сравнение позиций ролей, владелец сервера); запрещает ограничивать владельца

## Dependencies

### Repositories
- `MemberRepositoryProtocol` — получение участников сервера
- `ServerRepositoryProtocol` — получение сервера для проверки владельца
- `MemberRestrictionRepositoryProtocol` — CRUD ограничений участников
- `RestrictionRepositoryProtocol` — получение типа ограничения по ID
- `PermissionRepositoryProtocol` — получение прав по роли (`list_for_role`) и по коду (`get_by_code_bulk`)

## Method: `get_member(server_id: UUID, user_id: UUID) -> Member | None`

### Purpose
Возвращает участника сервера по ID пользователя; для публичных серверов возвращает None если участник не найден.

### Algorithm
1. Запросить участника через `member_repo.get_by_user_in_server(server_id, user_id)` (возможен None)
2. Запросить сервер через `server_repo.get(server_id)`
3. Если сервер не найден → `NotFoundException`
4. Если участник не найден:
   - **Сервер публичный** → вернуть `None`
   - **Сервер приватный** → `NotFoundException`
5. Вернуть участника

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Сервер не найден; участник не найден на приватном сервере |

## Method: `get_permissions(server_id: UUID, user_id: UUID) -> list[Permission]`

### Purpose
Возвращает список прав пользователя на сервере на основе его роли.

### Algorithm
1. Получить участника через `get_member(server_id, user_id)`:
   - Если `None` → вернуть пустой список `[]`
2. Получить `member.server` → `InternalLogicException` если None
3. Определить `is_owner` (сравнить `server.owner_id` с `user_id`)
4. Получить права роли через `permission_repo.list_for_role(member.server_role_id)`
5. Преобразовать Permission → PERMISSION enum через `_transform_permissions_to_enum()`
6. Применить `_compute_overwrites_enum(permission_codes, is_owner)` — если владелец или есть ADMINISTRATOR, возвращаются все права
7. Преобразовать PERMISSION enum → Permission модели через `_transform_enum_to_permissions()`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `InternalLogicException` | У участника нет привязанного сервера |

## Method: `get_permission_mask(server_id: UUID, user_id: UUID) -> int`

### Purpose
Возвращает битовую маску прав пользователя на сервере.

### Algorithm
1. Получить участника через `get_member(server_id, user_id)`:
   - Если `None` → вернуть `0`
2. Получить `member.server` → `InternalLogicException` если None
3. Определить `is_owner`
4. Получить права роли через `permission_repo.list_for_role(member.server_role_id)`
5. Преобразовать в битовую маску через `_transform_permission_to_mask()`
6. Применить `_compute_overwrites_mask(permission_mask, is_owner)` — если владелец или ADMINISTRATOR, возвращается полная маска

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `InternalLogicException` | У участника нет привязанного сервера |

## Method: `get_restrictions(server_id: UUID, user_id: UUID) -> list[MemberRestriction]`

### Purpose
Возвращает список активных ограничений участника на сервере.

### Algorithm
1. Попытаться получить участника через `get_member(server_id, user_id)`
   - Если `NotFoundException` → вернуть пустой список `[]`
2. Если участник `None` → вернуть `[]`
3. Вызвать `member_restriction_repo.list_for_member(member.id)`

### Exceptions
Нет (исключения перехватываются)

## Method: `get_restriction_mask(server_id: UUID, user_id: UUID) -> int`

### Purpose
Возвращает битовую маску ограничений участника на сервере.

### Algorithm
1. Получить участника через `get_member(server_id, user_id)`:
   - Если `None` → вернуть `0`
2. Получить список ограничений через `member_restriction_repo.list_for_member(member.id)`
3. Преобразовать коды ограничений в RESTRICTION enum и сериализовать в битовую маску

### Exceptions
Нет

## Method: `add_restriction(member_id: UUID, issuer_id: UUID, server_id: UUID, permission_mask: int, reason: str, expiration_date: datetime, restriction_id: UUID) -> MemberRestriction`

### Purpose
Накладывает ограничение на участника с проверкой прав выдающего и типов ограничений.

### Algorithm
1. Получить целевого участника через `member_repo.get(member_id)` → `NotFoundException` если None или `member.server_id != server_id`
2. Получить тип ограничения через `restriction_repo.get(restriction_id)` → `NotFoundException` если None
3. Проверить право: `PERMISSION.check_permission(permission_mask, f"restrict_{restriction.code}")` → `ForbiddenException` если нет права на данный тип
4. Получить выдающего участника через `member_repo.get(issuer_id)` → `InternalLogicException` если None
5. Получить сервер через `issuer_field.server` → `InternalLogicException` если None
6. Проверить возможность манипуляции через `_can_manipulate_restrictions(issuer_field, member_field, server_field)` → `ForbiddenException`
7. Создать ограничение через `member_restriction_repo.create(...)`:
   - `IntegrityForeignException` → оборачивается в `NotFoundException`
   - `IntegrityUnknownException` → оборачивается в `InternalLogicException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Целевой участник не найден; тип ограничения не найден; ошибка внешнего ключа при создании |
| `ForbiddenException` | Нет права на добавление ограничения данного типа; нет прав на манипуляцию ограничениями |
| `InternalLogicException` | Выдающий участник не найден; сервер не найден; ошибка целостности неизвестного типа |

## Method: `remove_restriction(member_id: UUID, issuer_id: UUID, server_id: UUID, member_restriction_id: UUID, permission_mask: int) -> None`

### Purpose
Снимает ограничение с участника с проверкой прав.

### Algorithm
1. Получить выдающего участника через `member_repo.get(issuer_id)` → `NotFoundException` если None
2. Получить ограничение через `member_restriction_repo.get(member_restriction_id)` → `NotFoundException` если None или `member_restriction.member_id != member_id`
3. Проверить право: `PERMISSION.check_permission(permission_mask, f"restrict_{restriction.code}")` → `ForbiddenException` если нет права на данный тип
4. Получить целевого участника через `member_restriction.member` → `InternalLogicException` если None или `member.server_id != server_id`
5. Получить сервер через `issuer_field.server` → `InternalLogicException` если None
6. Проверить возможность манипуляции через `_can_manipulate_restrictions(issuer_field, member_field, server_field)` → `ForbiddenException`
7. Удалить через `member_restriction_repo.delete(member_restriction_id)` → если не удалён, `NotFoundException`

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | Выдающий участник не найден; ограничение не найдено; ошибка удаления |
| `ForbiddenException` | Нет права на удаление ограничения данного типа; нет прав на манипуляцию ограничениями |
| `InternalLogicException` | Целевой участник или сервер не найдены через связи |
