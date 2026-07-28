# Document Type Templates & Rules

> Эталонная структура документации. Используется как справочник при создании и редактировании файлов.

---

### Тип 1: Модель — `docs/models/<kebab-case>.md`

Описывает доменную модель: поля, связи, DTO для CRUD.

#### Обязательная структура

```markdown
# <ModelName>

- **ORM file:** `src/core/models/<snake_case>.py`
- **Repo protocol:** `<ModelName>RepositoryProtocol`
- **Used by services:** `<Service1>`, `<Service2>`, ...

## Role
Одно-два предложения: что представляет модель и какую роль играет в системе.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | ... |
| ... | ... | ... |

## Relations

| Relation | Type | Description |
|----------|------|-------------|
| `related_name` | `list[RelatedModel]` | ... |
| `other` | `OtherModel \| None` | ... |

## Create/Update Models

### Create — `<Model>Create` (`src/core/models/<snake_case>.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| ... | ... | ... | ... | ... |

### Update — `<Model>Update` (`src/core/models/<snake_case>.py`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| ... | ... | ... | ... | ... |

> <Примечание о неизменяемых полях, если есть>

### Read — `<Model>` (`src/core/models/<snake_case>.py`)

| Field | Type | Notes |
|-------|------|-------|
| ... | ... | ... |
| `relations` | `list[...]` | Навигационное свойство |
```

#### Правила

- **Fields** — только прямые поля модели (не навигационные свойства)
- **Relations** — только связи с другими моделями (relationship)
- **Create** — все поля для создания; Required = Yes если нет default
- **Update** — только изменяемые поля; `None` для optional. Неизменяемые поля (id, FK) исключить, добавить примечание
- **Read** — все поля включая навигационные свойства (помечать как «Навигационное свойство»)
- Колонку **Notes** заполнять только если есть нетривиальная информация

---

### Тип 2: Репозиторий — `docs/repositories/<snake_case>.md`

Описывает интерфейс и реализацию репозитория: кастомные методы, eager loading.

#### Обязательная структура

```markdown
# <ModelName>Repository

**Protocol:** `src/core/interfaces/repo/<snake_case>.py`
**Implementation:** `src/infra/postgre/repo/<snake_case>.py`
**Model:** `<Model>` ([models/<model>.md](../models/<model>.md))

> **Note for agents:** New repositories should inherit from `BaseRepository[Model, CreateDTO, ReadDTO, UpdateDTO]` **and** the corresponding `*RepositoryProtocol`. The protocol provides the type-checkable contract; the base class provides the implementation. Only override or add methods specific to the entity. See [base.md](base.md) for inherited methods.

## Base Methods

Inherited from `BaseRepository` ([base.md](base.md)):

| Method | Signature | Notes |
|--------|-----------|-------|
| `get` | `(field_id: UUID) -> <Model> \| None` | Overridden with eager load flags |
| `get_list` | `(offset, limit, options, *where) -> Sequence[<Model>]` | |
| `create` | `(dto: <Model>Create) -> <Model>` | |
| `update` | `(dto: <Model>Update) -> <Model>` | |
| `delete` | `(field_id: UUID) -> bool` | |
| `exists` | `(field_id: UUID) -> bool` | |
| `count` | `(*where) -> int` | |

## Custom Methods

### `<method_name>`

```python
async def <method_name>(<params>) -> <return_type>
```

<Описание: что делает, когда используется, особые условия>

## Eager Loading Map

| Flag | Relationship |
|------|-------------|
| `load_<relation>` | `<Model>.<relation>` |
```

#### Правила

- **Base Methods** — всегда включать все 7 методов, даже если не переопределены
- Если `get` переопределён с eager load флагами — показать полную сигнатуру в Custom Methods
- Если `update` принимает ID отдельно (не через DTO) — отразить в Signature таблицы Base Methods
- **Custom Methods** — только методы, которых нет в BaseRepository
- **Eager Loading Map** — только если есть флаги eager loading; если нет — секцию не создавать
- Если нет ни кастомных методов, ни eager loading — оставить только Base Methods

---

### Тип 3: Сервис — `docs/modules/<feature>/service.md`

Описывает бизнес-логику сервиса: зависимости, алгоритмы методов, исключения.

#### Обязательная структура

```markdown
# <ServiceName> — Business Logic

## Overview
- **File:** `src/core/services/<snake_case>.py`
- **Private helper:** `_<helper_name>(...) -> <ReturnType>` — <краткое описание>

## Dependencies

### Repositories
- `<RepoProtocol>` — <кратко: для чего используется>

### Clients
- `<ClientName>` — `<method>()` (<transport>)

### Config
- `env.<setting>` — <описание флага>

## Method: `<method_name>(command: <CommandType>) -> <ReturnType>`

### Purpose
Одно предложение: что делает метод.

### Algorithm
1. <Шаг 1> → `<ExceptionType>` если условие
2. <Шаг 2>
3. ...

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | ... |
| `ForbiddenException` | ... |
```

#### Правила

- **Overview** — указать private helpers только если они нетривиальны
- **Dependencies** — группировать по категориям: Repositories, Clients, Config. Пустые категории не создавать
- **Purpose** — одно предложение, без деталей реализации
- **Algorithm** — нумерованный список, каждый шаг — атомарное действие
  - Указывать исключения inline: `→ ExceptionType` если условие
  - Не расписывать очевидное (создание DTO, возврат результата)
  - Фокус на бизнес-правилах, валидации, переходах состояний
- **Exceptions** — таблица всех возможных исключений метода (дублирует inline из Algorithm)
- Если метод не использует сервисный слой (например, health-check) — не создавать service.md

---

### Тип 4: Внешний контракт — `docs/modules/<feature>/api.md`

Описывает контракты: команды/запросы, результаты/ответы, поведение, исключения.

#### Обязательная структура

```markdown
# <Feature> — Queue Contracts

## Overview
- **Handler file:** `src/app/rabbit/api/<feature>.py`
- **Service file:** `src/core/services/<feature>.py` (опционально)
- **Commands file:** `src/core/commands/<feature>.py`
- **Results file:** `src/core/results/<feature>.py`

## Queues Summary

| Queue | Command | Result | Description |
|-------|---------|--------|-------------|
| `<queue.name>` | `<CommandName>` | `<ResultName>` | <Описание> |

---

## Queue: `<queue.name>`

### Command: `<CommandName>`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_data` | `AccessDataRequest` | Yes | |
| `field_name` | `Type` | Yes/No | <Описание> |

### Result: `<ResultName>`
| Field | Type | Description |
|-------|------|-------------|
| `field_name` | `Type` | <Описание> |

### Behavior
- <Ключевые особенности поведения>
- <Специфичные правила>

### Exceptions
| Exception | Condition |
|-----------|-----------|
| `NotFoundException` | ... |
| `ForbiddenException` | ... |
```

#### Правила

- **Overview** — обычно 4 строки; если нет service — пропустить Service file
- **Queues Summary** — таблица всех контрактов модуля
- Разделитель `---` между контрактами
- Для каждого контракта:
  - **Command** — все поля; `access_data` можно без Description
  - **Result** — поля результата; вложенные типы — inline списком: `**<NestedType>:** field1 (Type), field2 (Type)` или отдельной мини-таблицей
  - **Behavior** — только нетривиальная логика
  - **Exceptions** — все исключения с условиями
- Для пустых команд: `Пустая команда (без полей).`
- Если Result простой — можно без таблицы, одной строкой

#### Правила для Result-схем

- **Переиспользуемые схемы** (используются в >1 контракте или >1 модуле) — выносятся в `docs/_shared/<schema-name>.md`. В контракте даётся ссылка: `→ См. [_shared/<file>.md](../../_shared/<file>.md)`.
- **Уникальные схемы** (используются только в одном модуле) — полная таблица в первом появлении. В остальных контрактах модуля — ссылка на первое появление.
- **Вложенные типы** (>3 полей) — мини-таблицей в том же блоке или отдельным подзаголовком `### <NestedType>`.

#### Адаптация для HTTP/gRPC

| Исходный термин (RabbitMQ) | HTTP | gRPC |
|---------------------------|------|------|
| Queue | Endpoint | RPC |
| Command | Request Body | Request message |
| Result | Response | Response message |
| Queues Summary → | Endpoints Summary | RPCs Summary |

---

### Тип 5: Status Machine — `docs/statuses/<status-name>.md`

Описывает enum'ы с жизненным циклом, переходами и guard-проверками.

#### Обязательная структура

```markdown
# <StatusName> — State Machine

**Enum:** `path/to/enum.py:<line>`
**Transition config:** `path/to/config` (если декларативный)
**Validation:** `method()` — `path/to/validator.py:<line>`

Одно-два предложения: что моделирует статусная машина.

## States

| State | Description | Terminal |
|-------|-------------|----------|
| `STATE` | Описание | Yes/No |

## Allowed Transitions

```
     ASCII-граф переходов (опционально)
     ┌─────────────┐
     │  CREATED    │
     └──────┬──────┘
            ▼
     ┌─────────────┐
     │   IDLE      │
     └─────────────┘
```

### Transition Map

| From | To |
|------|----|
| `STATE_A` | `STATE_B`, `STATE_C` |
| `STATE_B` | *(terminal)* |

## Transition Triggers

| Transition | Trigger (Service Method) | Permission Required | Additional Guards |
|------------|-------------------------|---------------------|--------------------|

## Services That Guard on This Status (Read-Only)

| Service | Method(s) | Guarded States | Block Condition | Error Message |

## Validation Implementation

<как валидация реализована: конфиг → маппинг → проверка в ORM или сервисе>
```

#### Shared Enum docs — `docs/_shared/enums.md`

```markdown
# Enums

Все enum-ы определены как `str, enum.Enum` и сериализуются в строковые значения.

## <EnumName>
- **File:** `path/to/file.py`
- **Используется:** <где используется>
- **Подробно:** [statuses/<name>.md](../statuses/<name>.md) (если есть машина состояний)

| Value | Description |
|-------|-------------|

...
```

---

### Общие правила для всех типов

1. **Язык:** русский для описаний, английский для заголовков секций
2. **Ссылки на код:** всегда относительные пути от корня проекта в backticks
3. **Ссылки между doc-файлами:** относительные Markdown-ссылки
4. **Таблицы:** заголовки обязательны, выравнивание — по желанию
5. **Без комментариев** в таблицах, кроме колонки Notes/Description
6. **Без примеров кода** — только сигнатуры методов
7. **Без истории изменений** — документация отражает текущее состояние
8. **Не дублировать** информацию между файлами; ссылаться, а не копировать

---

## Quick Reference

### File naming conventions

| Тип | Паттерн имени | Пример |
|-----|---------------|--------|
| Model | `kebab-case.md` | `event-player.md` |
| Repository | `snake_case.md` | `team_player.md` |
| Module dir | `feature-name/` | `team-formation/` |
| Module api | `api.md` | `modules/event/api.md` |
| Module service | `service.md` | `modules/match/service.md` |
| Status | `kebab-case.md` | `event-status.md` |
| Shared | `kebab-case.md` | `event-detail.md`, `domain-exceptions.md` |
