# InviteRepository

**Protocol:** `src/core/interfaces/repo/invite.py`
**Implementation:** `src/infra/postgre/repo/invite.py`
**Model:** [Invite](../models/invite.md)

## Base Methods

Inherited from `BaseRepositoryImpl[Invite]` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(invite_id: UUID, /) -> Invite \| None` | Поиск по первичному ключу |
| `delete` | `(invite_id: UUID, /) -> bool` | Удаление по ID, возвращает `True` если запись удалена |

Методы `get_list`, `create`, `update`, `exists`, `count` в протоколе не объявлены — репозиторий использует собственные сигнатуры для кастомных операций.

## Custom Methods

### `get_by_key(key: str) -> Invite | None`
Поиск приглашения по строковому ключу.

- `SELECT … WHERE key = :key LIMIT 1`

### `list_for_server(server_id: UUID) -> Sequence[Invite]`
Список всех приглашений указанного сервера.

- `SELECT … WHERE server_id = :server_id`

### `create(server_id: UUID, use_limit: int, inviter_id: UUID | None = None, key: str | None = None) -> Invite`
Создаёт приглашение.

- Если `key` передан явно — вставка с `INSERT … RETURNING`. При нарушении уникальности ключа (SQLSTATE 23505) выбрасывает `IntegrityUniqueException`, при нарушении внешнего ключа (SQLSTATE 23503) — `IntegrityForeignException`, прочие ошибки — `IntegrityUnknownException`.
- Если `key` не указан — генерирует уникальный ключ (до 5 попыток через `secrets.token_urlsafe`). При коллизии ключа использует `ON CONFLICT DO NOTHING` и повторяет генерацию. Если после 5 попыток уникальный ключ не получен — выбрасывает `InviteUniqueException`.

**Exceptions:** `IntegrityUniqueException`, `IntegrityForeignException`, `IntegrityUnknownException`, `InviteUniqueException`

### `set_use_limit(invite: Invite, use_limit: int) -> Invite`
Устанавливает лимит использований приглашения. Отрицательное значение сбрасывается в 0.

- Мутирует переданный объект `invite` и вызывает `session.flush()`.

### `decrement_use_limit(invite: Invite) -> Invite`
Уменьшает лимит использований на 1 (если `use_limit` больше 0).

- `invite.use_limit -= 1` (только при `invite.use_limit > 0`)
- Мутирует переданный объект и вызывает `session.flush()`.

## Особенности реализации

- Репозиторий наследует `BaseRepositoryImpl[Invite]` и реализует `InviteRepositoryProtocol`.
- Метод `create` переопределён с полной сигнатурой (не использует `InviteCreate` DTO), так как включает генерацию ключа и обработку коллизий.
- Генерация ключа использует `secrets.token_urlsafe(12)` с удалением символов `-` и `_`.
- При вставке с явным ключом используется `INSERT` с `RETURNING`; при авто-генерации — `INSERT … ON CONFLICT DO NOTHING … RETURNING`.
- Метод `set_use_limit` не объявлен в `InviteRepositoryProtocol`, но реализован в классе и используется сервисами.
