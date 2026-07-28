# CustomRepository

**Protocol:** `src/core/interfaces/repo/custom.py`
**Implementation:** `src/infra/postgre/repo/custom.py`
**Model:** [Custom](../models/custom.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(custom_id: UUID, /) -> Custom \| None` | Поиск по первичному ключу |
| `delete` | `(custom_id: UUID, /) -> bool` | Удаление по первичному ключу. Возвращает `True`, если строка удалена |

## Custom Methods

### `list_for_member(member_id: UUID) -> Sequence[Custom]`
Возвращает все кастомные списки указанного участника.

**Алгоритм:**
1. `SELECT … WHERE member_id = :member_id` по таблице Custom
2. Возвращает все найденные записи

### `create(member_id: UUID, creator_id: UUID | None = None) -> Custom`
Создаёт кастомный список для участника.

**Алгоритм:**
1. Создаёт экземпляр `Custom(member_id, creator_id)`
2. Добавляет в сессию и выполняет `flush`
3. Загружает созданную запись через `get`
4. Если запись не найдена — `IntegrityUnknownException`

**Исключения:**

| Исключение | Условие |
|------------|---------|
| `IntegrityForeignException` | `member_id` или `creator_id` ссылаются на несуществующие записи (SQLSTATE 23503) |
| `IntegrityUnknownException` | Другая ошибка целостности при вставке |

### `set_creator(custom: Custom, creator_id: UUID) -> Custom`
Устанавливает нового создателя кастомного списка.

**Алгоритм:**
1. Если `custom.creator_id == creator_id` — возвращает объект без изменений
2. Иначе присваивает `custom.creator_id = creator_id`, выполняет `flush`
3. Возвращает обновлённый объект
