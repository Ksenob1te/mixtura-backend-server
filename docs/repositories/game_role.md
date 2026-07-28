# GameRoleRepository

**Protocol:** `src/core/interfaces/repo/game_role.py`
**Implementation:** `src/infra/postgre/repo/game_role.py`
**Model:** [GameRole](../models/game-role.md)

## Base Methods

Inherited from `BaseRepositoryImpl` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(role_id: UUID) -> GameRole \| None` | |
| `delete` | `(role_id: UUID) -> bool` | |

`get_list`, `update`, `exists`, `count` не реализованы — репозиторий использует собственные методы для модификации и выборки.

## Custom Methods

### `list_for_set(role_set_id: UUID) -> Sequence[GameRole]`
Список ролей для указанного набора ролей. Выполняет `SELECT` с фильтром по `role_set_id`.

### `create(name, role_set_id, min_in_team, max_in_team, icon_id, hidden) -> GameRole`
Создаёт новую игровую роль. После `flush` повторно загружает созданную роль через `get()`.

| Exception | Condition |
|-----------|-----------|
| `IntegrityForeignException` | `role_set_id` не существует (SQLSTATE 23503) |
| `IntegrityUnknownException` | Другая ошибка целостности |

### `set_name(role, name) -> GameRole`
Устанавливает название роли. Мутирует переданный объект `role` и выполняет `flush`.

### `set_icon(role, icon_id) -> GameRole`
Устанавливает иконку роли. Принимает `None` для сброса иконки.

### `set_hidden(role, hidden) -> GameRole`
Устанавливает флаг скрытия роли.

### `set_min(role, min_in_team) -> GameRole`
Устанавливает минимум участников в команде. Если `min_in_team` превышает текущий `max_in_team`, значение минимума приводится к `max_in_team`.

### `set_max(role, max_in_team) -> GameRole`
Устанавливает максимум участников в команде. Если `max_in_team` меньше текущего `min_in_team`, значение максимума приводится к `min_in_team`.

### `copy_role(template_role, new_role_set_id) -> GameRole`
Копирует роль-шаблон в новый набор ролей. Использует внутренний вызов `create()` с полями из `template_role`: `name`, `role_set_id`, `min_in_team`, `max_in_team`, `icon_id`, `hidden`.

## Особенности реализации

- **Сеттеры мутируют объект in-place:** все методы вида `set_*` принимают объект `GameRole` из ORM-сессии, изменяют его атрибут и вызывают `session.flush()`. Никакие дополнительные проверки на уровне репозитория не выполняются (кроме корректировки min/max в `set_min`/`set_max`).
- **Валидация min/max:** `set_min` и `set_max` содержат защиту от некорректного диапазона: если новое значение нарушает `min <= max`, одно из значений автоматически подгоняется под другое.
- **Нет методов `get_list`, `update`, `exists`, `count`:** репозиторий не использует общие CRUD-методы base-класса; все операции выполняются через специализированные методы.
- **`copy_role` объявлен в протоколе:** используется `GameService.copy_global_game()` при копировании глобальной игры в воркспейс.
