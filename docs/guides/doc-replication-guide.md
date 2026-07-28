# Agent Guide: How to Build This Documentation Structure on Any Project

> Эта инструкция описывает структуру и правила документации, которую нужно воспроизвести на новом проекте. Все шаблоны и правила встроены — не нужно знать проект-источник.

## 1. Architecture Overview

```
docs/
  INDEX.md                        # Навигация, все разделы в таблицах
  guides/
    structure.md                  # Шаблон этого же файла — правила и типы документов
  models/                         # Доменные модели — по файлу на модель
  statuses/                       # Статусные машины — машина = файл + INDEX.md
    INDEX.md                      # Обзор всех статусных машин
  _shared/                        # Переиспользуемые схемы, общие компоненты
  repositories/                   # Репозитории — по файлу на репозиторий
    base.md                       # Базовый репозиторий с generic CRUD
  modules/                        # Функциональные модули — папка на модуль
    <feature>/
      api.md                      # Внешние контракты (команды/запросы, результаты/ответы)
      service.md                  # Бизнес-логика (опционально — если модуль имеет сервисный слой)
```

## 2. Setup Steps (Sequential)

### Step 1: Analyse src/ structure

Изучи структуру исходного кода нового проекта. Определи:

1. **Система обмена сообщениями:** RabbitMQ очереди, Kafka топики, HTTP endpoints, gRPC методы? От этого зависит формат `api.md`.
2. **Слой бизнес-логики:** Сервисы/use cases с изолированными алгоритмами — будут `service.md`.
3. **Доменные модели:** Центральные сущности и их поля, связи, статусы.
4. **Репозитории/DAO/Data access:** Слой абстракции доступа к данным — будут `repositories/`.
5. **Статусные enum'ы:** Enum'ы с жизненным циклом и переходами — будут `statuses/`.
6. **Общие DTO/schemas:** Схемы, переиспользуемые в >1 модуле — вынести в `_shared/`.

### Step 2: Create directory structure

```bash
mkdir -p docs/models docs/statuses docs/_shared docs/repositories docs/modules docs/guides
```

### Step 3: Create `docs/guides/structure.md`

Скопируй **содержимое Раздела 3** этой инструкции — он содержит полные шаблоны и правила для каждого типа документов. Это будет эталон, на который ссылается `INDEX.md`.

### Step 4: Create `docs/INDEX.md`

Используй шаблон ниже. Заполни таблицы по мере создания файлов.

```markdown
# <Project Name> — Documentation Index

> **INSTRUCTION FOR AGENTS:** При внесении изменений в код ОБЯЗАТЕЛЬНО обновляйте соответствующие файлы документации.
>
> **NOTE FOR AGENTS:** Структура и содержание файлов документации описаны в [guides/structure.md](guides/structure.md). Перед созданием нового файла или редактированием существующего — ознакомьтесь с ней.
>
> | Изменение в коде | Что обновить |
> |------------------|--------------|
> | Новый/изменённый handler/endpoint | `<feature>/api.md` — контракты |
> | Новый/изменённый метод сервиса | `<feature>/service.md` — алгоритм, исключения, зависимости |
> | Новая/изменённая команда/DTO запроса | `<feature>/api.md` — схема Command/Request |
> | Новый/изменённый результат/DTO ответа | `<feature>/api.md` или перенести в `_shared/<schema>.md` если переиспользуется |
> | Новая/изменённая модель | `models/<model>.md` — поля, роль, связи |
> | Изменение общих схем | `_shared/<file>.md` |
> | Новый/изменённый репозиторий/DAO | `repositories/<name>.md` — методы, eager loading |
> | Новый модуль/сервис | Создать `<feature>/api.md` + `<feature>/service.md`, добавить в таблицу модулей |
> | Удаление кода | Удалить из соответствующих `.md` файлов |

## Modules

| Module | API Contracts | Service Logic |
|--------|--------------|---------------|
| <ModuleName> | [api.md](modules/<feature>/api.md) | [service.md](modules/<feature>/service.md) |

<!-- Для модулей без сервисного слоя — service.md не создавать, ячейку оставить пустой или прочерк -->

## Status Machines

> Подробные диаграммы переходов, триггеры, условия и guard-проверки для каждого статуса.

| Status | File | Brief |
|--------|------|-------|
| INDEX | [statuses/INDEX.md](statuses/INDEX.md) | Обзор всех статусных машин и их взаимодействий |
| <StatusName> | [statuses/<file>.md](statuses/<file>.md) | Краткое описание |

<!-- Если статусных машин нет — удали весь блок -->

## Shared Components

| Component | File | Brief |
|-----------|------|-------|
| <SchemaName> | [_shared/<file>.md](_shared/<file>.md) | Краткое описание |

## Domain Models

| Model | File | Brief |
|-------|------|-------|
| <ModelName> | [models/<file>.md](models/<file>.md) | Краткое описание |

## Repositories

> **Note for agents:** Новые репозитории должны наследоваться от `BaseRepository[Model, CreateDTO, ReadDTO, UpdateDTO]` (или аналога) **и** от соответствующего `*RepositoryProtocol`. Описывайте только кастомные методы и eager loading флаги — базовые CRUD методы уже задокументированы в [base.md](repositories/base.md).

| Repository | File | Brief |
|------------|------|-------|
| BaseRepository | [repositories/base.md](repositories/base.md) | Generic CRUD |
| <RepositoryName> | [repositories/<file>.md](repositories/<file>.md) | Краткое описание |

<!-- Если репозиториев нет — удали весь блок -->
```

### Step 5: Create module docs (iterative)

Для каждого функционального модуля:

1. Создай `docs/modules/<feature>/api.md` — внешние контракты (см. Тип 4 в Разделе 3)
2. Создай `docs/modules/<feature>/service.md` — бизнес-логика (см. Тип 3 в Разделе 3)
3. Добавь ссылки в таблицу Modules в INDEX.md

**Порядок:** сначала модули с самым простым контрактом (health, если есть), потом центральные (core entities), потом зависимые.

### Step 6: Create model docs

Для каждой доменной модели:

1. Создай `docs/models/<kebab-case>.md`
2. Следуй Тип 1 в Разделе 3
3. Добавь ссылку в таблицу Domain Models в INDEX.md

### Step 7: Create repository docs

Если в проекте есть слой репозиториев/DAO:

1. Создай `docs/repositories/base.md` — общий CRUD (шаблон ниже в Типе 2)
2. Для каждого репозитория — `docs/repositories/<snake_case>.md`
3. Следуй Тип 2 в Разделе 3
4. Добавь ссылки в таблицу Repositories в INDEX.md

**`docs/repositories/base.md` шаблон:**

```markdown
# BaseRepository

**Protocol:** `src/core/interfaces/repo/base.py`
**Implementation:** `src/infra/postgre/repo/base.py`

Generic CRUD with DTO mapping and integrity error handling. All repositories inherit from this class.

## Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get` | `(field_id: UUID, **eager) -> Model \| None` | Get by primary key |
| `get_list` | `(offset, limit, options, *where, **kwargs) -> Sequence[Model]` | Paginated list |
| `create` | `(dto: CreateDTO) -> Model` | Create entity from DTO |
| `update` | `(dto: UpdateDTO) -> Model` | Update entity from DTO |
| `delete` | `(field_id: UUID) -> bool` | Soft/hard delete |
| `exists` | `(field_id: UUID) -> bool` | Check existence |
| `count` | `(*where) -> int` | Count with filters |
```

### Step 8: Create status machine docs

Если в проекте есть enum'ы с жизненным циклом и переходами:

1. Создай `docs/statuses/INDEX.md` (шаблон ниже)
2. Для каждого статуса: `docs/statuses/<status-name>.md` (см. Тип 5 в Разделе 3)
3. Добавь ссылки в таблицу Status Machines в INDEX.md

**`docs/statuses/INDEX.md` шаблон:**

```markdown
# Status Machines

В системе <N> статус-перечислений, каждое со своей логикой переходов.

| Status | File | Source | Formal Validator | Documentation |
|--------|------|--------|------------------|---------------|
| `<StatusName>` | `<source_file.py>:<line>` | `<config>` or "Service guards only" | `<method>` or "Нет" | [<file>.md](<file>.md) |

## Cross-Object Status Interactions

<Какие статусы каких объектов взаимосвязаны и через какие сервисы>

## Implementation Notes

- Все enum-ы — `str, enum.Enum`; сериализуются как строки
- Есть/нет формальной машины состояний (`transition_to()`)
- Где тестируется валидация переходов
```

### Step 9: Create shared docs

Для каждой переиспользуемой схемы/компонента:

1. Создай `docs/_shared/<component>.md`

**Обязательные shared-файлы (если применимо):**

| Файл | Содержит |
|------|----------|
| `enums.md` | Все enum'ы, их значения, где используются. Ссылки на statuses/ для enum'ов с жизненным циклом |
| `domain-exceptions.md` | Иерархия исключений, типичные сценарии для каждого, формат ответа |
| `permission-bits.md` | Битовые маски прав и ограничений, helper functions, паттерн проверки доступа |
| `pagination.md` | Стандартная пагинация: поля, дефолты |
| `access-data.md` | Блок авторизации/контекста запроса |
| `response-wrapper.md` | Generic конверт ответа |
| `status-response.md` | Универсальный ответ с одним полем status |
| `<schema-name>.md` | Любая схема, используемая в >1 модуля |

### Step 10: Wire INDEX.md

Финально заполни все таблицы в `docs/INDEX.md`. Проверь:

- Все ссылки работают (относительно корня проекта)
- `_shared/` файлы имеют правильный уровень `../`
- Нет битых ссылок и отсутствующих файлов

### Step 11: Smoke test links

Проверь:

- Все относительные ссылки работают (в VSCode: Cmd+Click)
- После перемещения/переименования файлов — обнови ссылки в INDEX.md и во всех `_shared/` ссылках
- Не создавай файлов, на которые нет ссылок из INDEX.md

---

## 3. Document Type Templates & Rules

> Этот раздел — содержимое для `docs/guides/structure.md`. Включает полные шаблоны и правила для каждого типа документов.

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

## 4. Quick Reference

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

### Required files checklist

- [ ] `docs/INDEX.md` — главная навигация
- [ ] `docs/guides/structure.md` — описание типов документов (скопировать Раздел 3)
- [ ] `docs/_shared/enums.md` — все enum'ы
- [ ] `docs/_shared/domain-exceptions.md` — иерархия исключений
- [ ] `docs/_shared/permission-bits.md` — права доступа (если есть)
- [ ] `docs/repositories/base.md` — generic CRUD (если есть репозитории)
- [ ] Для каждого модуля: `docs/modules/<name>/api.md`
- [ ] Для каждого модуля с бизнес-логикой: `docs/modules/<name>/service.md`
- [ ] Для каждой модели: `docs/models/<name>.md`
- [ ] Для каждого репозитория: `docs/repositories/<name>.md`
- [ ] Если есть статусные enum'ы: `docs/statuses/INDEX.md` + по файлу на статус
