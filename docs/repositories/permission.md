# PermissionRepository

**Protocol:** `src/core/interfaces/repo/permission.py`
**Implementation:** `src/infra/postgre/repo/permission.py`
**Model:** [Permission](../models/permission.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(permission_id: UUID, /) -> Permission \| None` | |
| `delete` | `(permission_id: UUID, /) -> bool` | |

## Custom Methods

### `get_by_code(code: str) -> Permission | None`
Получает право по коду.

### `get_by_code_bulk(code_names: list[str]) -> Sequence[Permission]`
Получает несколько прав по списку кодов.

### `list_all() -> Sequence[Permission]`
Список всех прав.

### `list_for_role(server_role_id: UUID | None) -> Sequence[Permission]`
Список прав, назначенных роли сервера.

### `create(code: str) -> Permission`
Создаёт новое право. `code` — строковый код из `PERMISSION` StrEnum. Выбрасывает `IntegrityUniqueException` при дубликате кода.

### `assign_to_role(permission_id: UUID, server_role_id: UUID) -> None`
Назначает право роли сервера (через junction `ServerRolePermission`). Использует `INSERT … ON CONFLICT DO NOTHING`. Выбрасывает `IntegrityForeignException`, если permission или server_role не найдены.

### `remove_from_role(permission_id: UUID, server_role_id: UUID) -> bool`
Отзывает право у роли сервера. Возвращает `True`, если право было отозвано.

### `bulk_assign_to_role(permission_ids: list[UUID], server_role_id: UUID) -> None`
Массово назначает права роли. Использует `INSERT … ON CONFLICT DO NOTHING` для всех переданных идентификаторов. Выбрасывает `IntegrityForeignException`, если какой-либо permission или server_role не найдены.

### `bulk_remove_from_role(permission_ids: list[UUID], server_role_id: UUID) -> int`
Массово отзывает права у роли. Возвращает количество отозванных прав.

### `bulk_set_for_role(permission_ids: list[UUID], server_role_id: UUID) -> None`
Устанавливает набор прав для роли: добавляет новые (через `bulk_assign_to_role`), удаляет отсутствующие (через `bulk_remove_from_role`).
