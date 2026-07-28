# Architecture Guide — Async Python Service Template

> A reusable reference for layered async Python backends.
> Works with **FastAPI** (HTTP), **FastStream** (message broker over RabbitMQ), or both side by side.
> Infrastructure components (Redis, RabbitMQ, external clients) are independent add-ons — include only what your project actually needs.

**Layering:**
- `src/core/` — domain layer. Zero imports from `infra` or `app`. Houses domain DTOs, business logic (services), repository/client/store protocols, and the generic `ResponseMessage` envelope returned by every handler.
- `src/infra/` — driven adapters: Postgres, Redis, outbound clients to external services. Things the system *calls out to*.
- `src/app/` — the system's entrypoints ("output"): FastAPI routers, FastStream handlers, their app factories, and the **external-facing** request/response/message models exposed at the boundary. Things that *call into* the system.

Swapping FastAPI for FastStream (or adding one alongside the other), or dropping Redis entirely, should never require touching `src/core/`.

---

## 1. Project Identity

Fill this in per project. Example shape:

| Property | Choice |
|---|---|
| **Transport** | HTTP via FastAPI, and/or async messaging via FastStream (RabbitMQ) — both live in `src/app/`. Pick one, or run both; the core/service layer doesn't know or care which. |
| **Language** | Python ≥3.11 (async-first) |
| **Package mgr** | `uv` (uv.lock, `uv sync`, `uv run`) |
| **ORM** | SQLAlchemy 2.0 async (`asyncpg`) |
| **Schema/validation** | Pydantic v2 (core DTOs, external app-layer schemas, settings, commands, results) |
| **Config** | pydantic-settings (env vars) + optional static INI/YAML for state machines |
| **Cache / ephemeral store** *(optional)* | Redis — only add if the project needs caching or short-lived task/variant stores |
| **Message broker** *(optional)* | RabbitMQ via FastStream — only add if the project needs async messaging or RPC between services |
| **DB migrations** | Alembic async (`async_engine_from_config` + `NullPool`) |
| **Testing** | pytest + testcontainers (Postgres container per session) |

Only `core/` and `infra/postgre/` are treated as mandatory below. `app/http/`, `app/rabbit/`, `infra/redis/`, `infra/clients/` are opt-in.

---

## 2. High-Level Architecture

```mermaid
flowchart TD
    subgraph External
        HTTP[HTTP clients]
        MQ["RabbitMQ (optional)"]
        R["Redis (optional)"]
    end

    subgraph app["src/app/ — entrypoints (\"output\")"]
        API["http/*.py\nFastAPI routers + external req/resp models (optional)"]
        RM["rabbit/main.py\nFastStream Broker + Lifespan (optional)"]
        RA["rabbit/api, models/*.py\nHandlers + external message models (optional)"]
    end

    subgraph infra["src/infra/ — driven adapters"]
        PGR[postgre/repo/*.py\nRepository Impl]
        PGM[postgre/models/*.py\nORM Models]
        PGE[postgre/engine.py\nEngine + Session]
        RE["redis/engine.py (optional)"]
        RS["redis/*.py Stores (optional)"]
        CL[clients/*.py\nOutbound ext. service clients]
    end

    subgraph core["src/core/"]
        SVC[services/*.py\nBusiness Logic]
        REPO_IFACE[interfaces/repo/*.py\nRepo & Store Protocols]
        CL_IFACE[interfaces/clients/*.py\nClient Protocols (optional)]
        ACP[access.py\nPermission functions]
        DTO[models/*.py\nDomain DTOs]
        CMD[commands/*.py\nInput DTOs]
        RSLT[results/*.py\nOutput DTOs]
        EXC[exceptions.py\nDomain Exceptions]
        RSP[response.py\nResponseMessage envelope]
    end

    subgraph config["src/env_config.py"]
        ENV[Env singleton\npydantic-settings]
    end

    HTTP --> API
    MQ -.-> RM
    RM -.-> RA
    API --> SVC
    RA -.-> SVC
    SVC --> REPO_IFACE
    SVC -.-> CL_IFACE
    REPO_IFACE --> PGR
    PGR --> PGM
    PGM --> PGE
    CL_IFACE --> CL
    SVC --> CL
    SVC -.-> RS
    RS -.-> RE
    RE -.-> R
    ENV --> API
    ENV --> RM
    ENV --> PGE
    ENV --> SVC
```

Dashed arrows = optional, present only if the project uses messaging and/or Redis.

---

## 3. Directory Layout

```
service/
├── src/
│   ├── core/                          # DOMAIN LAYER — zero infra/app imports
│   │   ├── models/                    #   Domain DTOs (colocated enums)
│   │   ├── commands/                  #   Input DTOs for service methods
│   │   ├── results/                   #   Output DTOs (views, flattened)
│   │   ├── services/                  #   Business logic (orchestrates repos)
│   │   ├── interfaces/
│   │   │   ├── repo/                  #   Repository protocols (typing.Protocol)
│   │   │   └── clients/               #   External service protocols
│   │   ├── exceptions.py              #   DomainException hierarchy
│   │   └── response.py                #   Generic response envelope
│   ├── infra/                         # INFRASTRUCTURE LAYER — driven adapters
│   │   ├── postgre/                   # ← mandatory
│   │   │   ├── models/                #   SQLAlchemy ORM models
│   │   │   ├── repo/                  #   Repository implementations
│   │   │   ├── engine.py              #   Async engine + session manager
│   │   │   └── exceptions.py          #   Integrity error types
│   │   ├── rabbit/                    # ← only if using a message broker
│   │   │   └── rpc_client.py          #   Async RPC client (only if req/reply is needed)
│   │   ├── redis/                     # ← only if you need caching/ephemeral stores
│   │   │   ├── engine.py              #   Redis session manager
│   │   │   └── *.py                   #   Stores
│   │   └── clients/                   #   Outbound clients to external services
│   │       └── *.py                   #   (implement src/core/interfaces/clients protocols)
│   ├── app/                           # ENTRYPOINT LAYER — system's "output": listeners + external models
│   │   ├── http/                      # ← only if exposing an HTTP API
│   │   │   ├── main.py                #   FastAPI app factory
│   │   │   ├── api/                   #   FastAPI routers
│   │   │   └── models/                #   External request/response schemas (API contract)
│   │   └── rabbit/                    # ← only if using a message broker
│   │       ├── main.py                #   FastStream app factory
│   │       ├── api/                   #   Message handlers
│   │       └── models/                #   External message payload schemas (contract)
│   ├── dependency.py                  # DI wiring, shared by app/http and app/rabbit
│   ├── env_config.py                  # Config singleton (pydantic-settings)
│   ├── logging_setup.py               # optional: structured logging bootstrap
│   └── config/                        # optional: .ini/.yaml for state machines etc.
├── start.py                           # Entrypoint
├── entrypoint.sh                      # Docker CMD: migrations + start.py
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── repo/
│   └── services/
├── pyproject.toml
├── pytest.ini
└── Dockerfile

`app/http/`, `app/rabbit/`, `infra/redis/`, `infra/postgre/` are independent — add the folders your project actually needs. `core/` stay regardless of transport.

---

## 4. Core Pattern: Four-File Mirror per Entity

Every domain entity (e.g. `Event`, `Player`, `Order`, …) is structured as **four files** with the same snake_case name:

| Layer | Path | Suffix | Example | Role |
|---|---|---|---|---|
| DTO/Enums | `src/core/models/<entity>.py` | — | `event.py` | Pydantic models (`Event`, `EventCreate`, `EventUpdate`) + colocated enums |
| Protocol | `src/core/interfaces/repo/<entity>.py` | — | `event.py` | `EventRepositoryProtocol` — `typing.Protocol` |
| ORM Model | `src/infra/postgre/models/<entity>.py` | `Model` | `event.py` → `EventModel` | SQLAlchemy `DeclarativeBase` subclass |
| Repository | `src/infra/postgre/repo/<entity>.py` | — | `event.py` → `EventRepository` | `BaseRepository[...]` + `*RepositoryProtocol` implementation |

**Rule:** `src/core/` **never imports** from `src/infra/` or `src/app/`. Dependencies flow **inward**: `app` (listeners) → `core` (services → protocols → DTOs) ← `infra` (implementations).
**Rule:** `src/infra/postgre/models/__init__.py` re-exports **only** `*Model` classes. Import domain DTOs from `src.core.models`.
**Rule:** Barrel exports via `__init__.py` are explicit: `__all__` lists every symbol.

This pattern is identical whether the entity is exposed over HTTP, over a message broker, or both — that decision is made entirely in `src/app/`.


### 4a. Permission / Access Module (Optional)

Cross-cutting permission logic lives as **pure functions in a single core module**, not scattered across services. The module receives domain data (event, organizer list, access credentials) and returns a boolean — no state, no I/O.

```python
# src/core/interfaces/repo/access.py
def is_same_server(event: Event, access: AccessData) -> bool: ...
def has_event_admin_permission(access: AccessData, event: Event) -> bool: ...
```

**Conventions:**
- One file per bounded context (e.g., `access.py` for event‑related permissions). If the domain has multiple independent permission domains, split per domain.
- Functions are stateless and synchronous — they compute a yes/no from in‑memory data already loaded by the service.
- Guards are called in services (step 2 of the service pattern in §8), never in handlers or repositories.
- Permission bits, roles, or restriction enums are colocated in the same file or in `src/core/models/`.

---

## 5. Domain DTO Layer (`src/core/models/`)

### CRUD Triplet Pattern

Every mutable entity has three DTOs:

```python
# src/core/models/event.py

class Event(BaseModel):
    """Read model — mirrors what the repo returns (all fields)."""
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    title: str
    status: EventStatus
    organizer_id: UUID
    created_at: datetime
    teams: list["Team"] = Field(default_factory=list)


class EventCreate(BaseModel):
    """Create payload — only writable fields, validators for business rules."""
    title: str = Field(min_length=1, max_length=256)
    match_type: EventMatchType


class EventUpdate(BaseModel):
    """Update payload — all fields optional (partial update)."""
    title: str | None = None
    match_type: EventMatchType | None = None
```

**Conventions:**
- Enums are `str` subclasses of `enum.Enum`, colocated in the entity file.
- `from_attributes=True` enables Pydantic's ORM-mode validation (used in repos).
- Forward references (`"Team"`) resolved via `model_rebuild()` in `__init__.py`.
- **Flat DTOs** (no ORM counterpart) omit CRUD suffixes and use `model_config = {"extra": "forbid"}` for strict schemas.

These are **domain** DTOs — internal shape. They are not automatically the wire format; see §6.

---

## 6. External Model Boundary (`src/app/*/models/`)

`src/app/http/models/` and `src/app/rabbit/models/` hold the **contract exposed to the outside world** — HTTP request/response bodies, message payloads. They live next to the listeners that use them, in `app/`, not in `core/` or `infra/`.

Why keep them separate from `core/commands` and `core/results` instead of reusing those directly:
- The external contract (API/message schema) is something you version and support for consumers; the internal Command/Result shape is free to change as the domain evolves.
- Renaming a field, splitting one endpoint into two, or adding a transport-specific validation rule shouldn't ripple into `src/core/services`.

```python
# src/app/http/models/player.py
class AddPlayerRequest(BaseModel):
    """External HTTP request contract."""
    member_id: UUID
    role: str

class PlayerResponse(BaseModel):
    """External HTTP response contract."""
    id: UUID
    member_id: UUID
    status: str
```

```python
# src/app/http/api/player.py
router = APIRouter()

@router.post("/players", response_model=PlayerResponse)
async def add_player(payload: AddPlayerRequest, service: PlayerServiceDependency):
    command = AddPlayerCommand(member_id=payload.member_id, role=payload.role)
    result = await service.add_player(command)
    return PlayerResponse(id=result.player_id, member_id=payload.member_id, status="added")
```

**Rule — every endpoint declares a strict response schema, no exceptions:**
- FastAPI: `response_model=<Schema>` on the decorator, where `<Schema>` is a concrete Pydantic model from `app/http/models/`. `dict`, `dict[str, Any]`, or omitting `response_model` entirely are all forbidden — each one silently breaks OpenAPI generation (no schema, no example, no client codegen) and gives up FastAPI's response filtering/validation.
- FastStream: the handler's return type annotation (`-> ResponseMessage[<Schema>]`) serves the same role — same rule applies to `<Schema>`.
- **When no schema exists yet:** look at what the service/repo actually returns (the `Result`/domain DTO fields) and write a Pydantic model that mirrors that shape — don't stub it as `dict` "for now." If a reviewer flags a missing or weak response type, the fix is a real model derived from the data, never a widened type like `dict[str, Any]` — that satisfies the type checker but is exactly the anti-pattern this rule exists to prevent (see §15.11).

Same pattern for FastStream, with message models instead of HTTP schemas:

```python
# src/app/rabbit/models/player.py
class AddPlayerMessage(BaseModel):
    member_id: UUID
    role: str

class PlayerAddedMessage(BaseModel):
    player_id: UUID
    status: str
```

```python
# src/app/rabbit/api/player.py
router = RabbitRouter()

@router.handle("player.add")
async def handle_add_player(
    payload: AddPlayerMessage, service: PlayerServiceDependency
) -> ResponseMessage[PlayerAddedMessage]:
    command = AddPlayerCommand(member_id=payload.member_id, role=payload.role)
    result = await service.add_player(command)
    return ResponseMessage(status=200, message=PlayerAddedMessage(player_id=result.player_id, status="added"))
```

**Pragmatic exception:** if an endpoint's external contract is genuinely identical to its `Command`/`Result`, it's fine to use the core DTO directly at the boundary rather than hand-writing a pass-through duplicate — but keep the mapping seam in mind for the day the two need to diverge.

---

## 7. Repository Pattern

### 7a. Protocol (Interface)

```python
# src/core/interfaces/repo/player.py
from typing import Protocol

class PlayerRepositoryProtocol(Protocol):
    async def get(self, player_id: UUID, load_roles: bool = False) -> EventPlayer | None: ...
    async def get_list(
        self, offset: int = 0, limit: int | None = 100,
        options: list[Any] | None = None, *where_clauses: Any
    ) -> Sequence[EventPlayer]: ...
    async def create(self, dto: EventPlayerCreate) -> EventPlayer: ...
    async def update(self, dto: EventPlayerUpdate) -> EventPlayer: ...
    async def delete(self, player_id: UUID) -> bool: ...
    async def exists(self, player_id: UUID) -> bool: ...
    async def count(self, *where_clauses: Any) -> int: ...
    # Domain-specific queries
    async def list_by_event(self, event_id: UUID, ...) -> Sequence[EventPlayer]: ...
```

**Key decisions:**
- **No generics** at the protocol level — each protocol references exact DTO types. Concrete > abstract when it eliminates `TypeVar` chains.
- `load_*` flags on `get()` — **opt-in eager loading**. Relationship columns use `lazy="noload"`; no lazy-loading proxies.
- `get_list()` exposes `*where_clauses: Any` as the escape hatch for simple filters.

### 7b. BaseRepository (Generic CRUD)

```python
# src/infra/postgre/repo/base.py
from typing import Any, Generic, Mapping, Sequence, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import Base
from ..exceptions import IntegrityForeignException, IntegrityUniqueException, IntegrityUnknownException

ModelType = TypeVar("ModelType", bound=Base)
CreateDTO = TypeVar("CreateDTO", bound=BaseModel)
ReadDTO = TypeVar("ReadDTO", bound=BaseModel)
UpdateDTO = TypeVar("UpdateDTO", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateDTO, ReadDTO, UpdateDTO]):
    model: Type[ModelType]
    dto_model: Type[ReadDTO]

    def __init__(self, session: AsyncSession):
        self._session = session
        if not hasattr(self, "model"):
            raise NotImplementedError("Repository must define 'model' class attribute")
        if not hasattr(self, "dto_model"):
            raise NotImplementedError("Repository must define 'dto_model' class attribute")

    async def _flush(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException() from exc
            if sql_state == "23505":
                raise IntegrityUniqueException() from exc
            raise IntegrityUnknownException() from exc

    async def _get_model(self, field_id: UUID, options: list[Any] | None = None) -> ModelType | None:
        stmt = select(self.model).where(getattr(self.model, "id") == field_id)
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalar(stmt)
        return result

    def _to_dto(self, obj: Any) -> ReadDTO:
        return self.dto_model.model_validate(obj, from_attributes=True)

    async def _get(self, field_id: UUID, options: list[Any] | None = None) -> ReadDTO | None:
        obj = await self._get_model(field_id, options=options)
        return self._to_dto(obj) if obj else None

    async def get(self, field_id: UUID) -> ReadDTO | None:
        return await self._get(field_id)

    async def _list_model(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        if options:
            stmt = stmt.options(*options)
        if order_by is not None:
            stmt = stmt.order_by(order_by)

        result = await self._session.scalars(stmt)
        return result.all()

    async def get_list(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ReadDTO]:
        items = await self._list_model(offset, limit, options, *where_clauses, order_by=order_by)
        return [self._to_dto(item) for item in items]

    def _dto_to_data(self, dto: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(dto, "model_dump"):
            raw_data = dto.model_dump(exclude_unset=exclude_unset)
        elif isinstance(dto, Mapping):
            raw_data = dict(dto)
        else:
            raw_data = dict(dto.__dict__)

        column_names = set(self.model.__mapper__.columns.keys())
        return {k: v for k, v in raw_data.items() if k in column_names}

    async def create(self, dto: CreateDTO) -> ReadDTO:
        create_data = self._dto_to_data(dto)
        obj = self.model(**create_data)
        self._session.add(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def update(self, dto: UpdateDTO) -> ReadDTO:
        update_data = self._dto_to_data(dto, exclude_unset=True)
        obj = self.model(**update_data)
        obj = await self._session.merge(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def delete(self, field_id: UUID) -> bool:
        obj = await self._get_model(field_id)
        if obj:
            await self._session.delete(obj)
            await self._flush()
            return True
        return False

    async def exists(self, field_id: UUID) -> bool:
        stmt = select(func.count()).select_from(self.model).where(getattr(self.model, "id") == field_id)
        count = await self._session.scalar(stmt)
        return (count or 0) > 0

    async def count(self, *where_clauses: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        val = await self._session.scalar(stmt)
        return val or 0
```

### 7c. Concrete Repository

> **Crucial:** every concrete repository MUST inherit its `*RepositoryProtocol` **in addition to** `BaseRepository`. This makes the structural contract enforceable by type checkers and prevents drift between the interface and the implementation.

```python
# src/infra/postgre/repo/player.py
from src.core.interfaces.repo.player import PlayerRepositoryProtocol

class PlayerRepository(
    BaseRepository[EventPlayerModel, EventPlayerCreate, EventPlayer, EventPlayerUpdate],
    PlayerRepositoryProtocol,
):
    model = EventPlayerModel
    dto_model = EventPlayer

    async def get(self, player_id: UUID, load_roles: bool = False) -> EventPlayer | None:
        options = [selectinload(EventPlayerModel.roles)] if load_roles else None
        return await self._get(player_id, options)

    async def list_by_event(
        self, event_id: UUID, status: EventPlayerStatus | None = None
    ) -> Sequence[EventPlayer]:
        clauses = [EventPlayerModel.event_id == event_id]
        if status is not None:
            clauses.append(EventPlayerModel.status == status)
        return await self.get_list(*clauses)
```

**Key decisions:**
- **No lazy loading** — all `relationship()` use `lazy="noload"`. Every join is explicit via `selectinload()` in override methods.
- **Integrity errors** are caught in `_flush()` and re-raised as typed exceptions: `IntegrityForeignException`, `IntegrityUniqueException`.
- **Session scope** — every repo receives an `AsyncSession` in `__init__`. No engine access.

---

## 7d. Store Pattern (Optional — Ephemeral Storage)

For ephemeral data (caches, short-lived task state, computed variants) use a **two-file pattern** mirroring the repo split — protocol in core, implementation in infra — but without ORM/DTO CRUD. Stores hold transient state, typically backed by Redis.

| Layer | Path | Example | Role |
|---|---|---|---|
| Protocol | `src/core/interfaces/repo/<entity>.py` | `team_formation_variant.py` | `TeamFormationVariantStoreProtocol` — `typing.Protocol` with `get`, `save`, `delete` |
| Implementation | `src/infra/redis/<entity>.py` | `team_formation_variant.py` | `TeamFormationVariantStore` — Redis-backed store |

**Conventions:**
- Protocol methods mirror the key‑value pattern: `save(key, value, ttl_seconds)`, `get(key)`, `delete(key)`.
- TTL is mandatory for any cached data — never store indefinitely.
- The store implementation receives a Redis client in `__init__`, not a full engine.
- Store protocols live in `src/core/interfaces/repo/` (same directory as repo protocols) since services consume them interchangeably — but see §15.15 for the distinction.
- Barrel exports and `model_rebuild()` rules from §4 apply identically.

```python
# src/core/interfaces/repo/team_formation_variant.py
from typing import Protocol

class TeamFormationVariantStoreProtocol(Protocol):
    async def save(self, key: str, variant: FormationVariant, ttl_seconds: int) -> None: ...
    async def get(self, key: str) -> FormationVariant | None: ...
    async def delete(self, key: str) -> None: ...


# src/infra/redis/team_formation_variant.py
class TeamFormationVariantStore:
    def __init__(self, redis: Redis):
        self._redis = redis

    async def save(self, key: str, variant: FormationVariant, ttl_seconds: int) -> None:
        data = variant.model_dump_json()
        await self._redis.setex(key, ttl_seconds, data)

    async def get(self, key: str) -> FormationVariant | None:
        data = await self._redis.get(key)
        if data is None:
            return None
        return FormationVariant.model_validate_json(data)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)
```

**When to use a Store vs a Repository:**
- **Repository** — authoritative persistence (Postgres). CRUD over domain entities with transactions, integrity checks, and relationships.
- **Store** — ephemeral or derived data (Redis). Key-value access with TTL. No transactions, no relationships, no integrity constraints.
- If data survives a restart and needs queryability beyond key lookup, it is not a Store — use a Repository.


## 7e. External Client Protocols (Optional)

Protocols for outbound calls to external services (RPC, HTTP, message publish) follow the same interface–implementation split as repositories, but their protocols belong in `src/core/interfaces/clients/`, **not** in `repo/`:

| Layer | Path | Example | Role |
|---|---|---|---|
| Protocol | `src/core/interfaces/clients/<service>.py` | `rating.py` | `RatingClientProtocol` — `typing.Protocol` with methods for external calls |
| Implementation | `src/infra/clients/<service>.py` | `rating.py` | `RatingClient` — concrete client (RabbitMQ RPC, HTTP, etc.) |

```python
# src/core/interfaces/clients/rating.py
class RatingClientProtocol(Protocol):
    async def calculate_effective_ratings(self, draft_id: UUID) -> RatingResult: ...


# src/infra/clients/rating.py
class RatingClient(RatingClientProtocol):
    def __init__(self, rpc_client: RabbitRpcClient, broker: RabbitBroker):
        ...

    async def calculate_effective_ratings(self, draft_id: UUID) -> RatingResult:
        # Non-blocking RPC over RabbitMQ
        ...
```

**Key rules:**
- Protocols live in `src/core/interfaces/clients/`, **not** in `interfaces/repo/`. Repository protocols describe CRUD over persistent entities; client protocols describe interactions with external systems.
- Implementations receive transport primitives (broker, HTTP session, RPC client) in `__init__`, never the full engine or connection string.
- If a client publishes messages and awaits a reply, use an `RpcClient` abstraction (see §11b). If it only publishes (fire-and-forget), inject the broker directly.
- Wired through `dependency.py` alongside repos and stores — same `Depends` + `Annotated` pattern.

**Common mistake:** placing `RatingClientProtocol` or `BalancerRequestRepositoryProtocol` (which is actually a client, not a repo) in `core/interfaces/repo/`. The distinction matters:
- **Repo protocol** → CRUD over domain entities backed by Postgres.
- **Client protocol** → call to an external system or service (RabbitMQ RPC, HTTP API, gRPC).
- **Store protocol** → ephemeral key-value with TTL backed by Redis (see §7d).

If a protocol does not have a corresponding ORM model and SQL table, it probably belongs in `interfaces/clients/` or as a Store — not in `interfaces/repo/`.

## 8. Service Layer

```python
# src/core/services/player.py
class PlayerService:
    def __init__(
        self,
        event_repo: EventRepositoryProtocol,
        player_repo: PlayerRepositoryProtocol,
    ):
        ...  # constructor injection — repos wired by dependency.py

    async def add_player(self, command: AddPlayerCommand) -> PlayerAddResult:
        # 1. Fetch aggregate
        event = await self._event_repo.get(command.event_id, load_organizers=True)
        # 2. Authorize
        if not has_event_admin_permission(command.access_data, event):
            raise ForbiddenException(...)
        # 3. Validate state
        if event.status != EventStatus.REGISTRATION:
            raise BadRequestException(...)
        # 4. Execute
        created = await self._player_repo.create(EventPlayerCreate(member_id=command.member_id, ...))
        # 5. Return result DTO
        return PlayerAddResult(player_id=created.id, ...)
```

**Pattern — every service method:**
1. **Fetch** — load the aggregate from repo (with relevant `load_*` flags).
2. **Authorize** — permission checks → `ForbiddenException`.
3. **Validate** — state machine guards, duplicate checks → `BadRequestException`, `ConflictException`.
4. **Execute** — call repo methods with Create/Update DTOs.
5. **Return** — build result DTO from repo output.

**Layers never mix:**
- Services import from `src.core.*` only (models, commands, results, interfaces) — never from `src.app.*` or `src.infra.*` directly.
- **Zero `fastapi`, `faststream`, `sqlalchemy`, `asyncpg`, `redis` imports in core** — this is what makes the transport swap possible without touching business logic.
- External service calls go through protocol interfaces — implementations live in `src/infra/clients/`.

---

## 9. Dependency Injection

FastAPI and FastStream both use an (almost) identical `Depends` + `Annotated` pattern, so the same `src/dependency.py` module works for either — only the import of `Depends` changes. `dependency.py` stays at `src/` root (not inside `app/`) since it's shared plumbing that wires `infra` implementations into `core` protocols, for consumption by whichever listeners live in `app/`.

```python
# src/dependency.py
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

# FastAPI:
# from fastapi import Depends
# FastStream:
# from faststream import Depends

# 1. Session providers
async def get_db_session() -> AsyncSession:
    async with session_manager.session() as session:
        yield session
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]

# 2. Repository providers
async def get_player_repository(session: DatabaseSession) -> PlayerRepositoryProtocol:
    return PlayerRepository(session)
PlayerRepositoryDependency = Annotated[PlayerRepositoryProtocol, Depends(get_player_repository)]

# 3. Service providers
async def get_player_service(
    player_repo: PlayerRepositoryDependency,
) -> PlayerService:
    return PlayerService(player_repo)
PlayerServiceDependency = Annotated[PlayerService, Depends(get_player_service)]
```

Listeners in `src/app/` inject the same alias regardless of transport (full request/response mapping shown in §6):

```python
# src/app/http/api/player.py
@router.post("/players", response_model=PlayerResponse)  # response_model always required — see §6
async def add_player(payload: AddPlayerRequest, service: PlayerServiceDependency):
    ...

# src/app/rabbit/api/player.py
@router.handle("player.add")
async def handle_add_player(payload: AddPlayerMessage, service: PlayerServiceDependency) -> ResponseMessage[PlayerAddedMessage]:
    ...
```

**Three layers of aliases, same as always:**
1. **Session** — `DatabaseSession`, `RedisSession` *(only if Redis is in use)*
2. **Repository/Client/Store** — `EventRepositoryDependency`, `RatingClientDependency`, …
3. **Service** — `EventServiceDependency`, `PlayerServiceDependency`, …

---

## 10. Configuration

```python
class PostgresConfig(LocalSettings):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

class Env(LocalSettings):
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    # Add only the sub-configs your project actually uses:
    # redis: RedisConfig = Field(default_factory=RedisConfig)
    # rabbit: RabbitConfig = Field(default_factory=RabbitConfig)
    # event_flow: EventFlowConfig = Field(default_factory=EventFlowConfig.load_from_ini)  # optional state machine

env = Env.load()  # module-level singleton
```

**Pattern:**
- Each infra dependency gets its own sub-config with a `.url` property.
- `Env` composes them — single import target (`from src.env_config import env`), used by both `src/infra/*` and `src/app/*`.
- If a project doesn't use Redis/RabbitMQ/a state machine, simply don't declare that sub-config — don't keep dead fields around "just in case".

### 10a. State Machine Config (Optional)

An INI/YAML file for explicit status transitions is worth adding when the domain has complex state machines beyond a simple enum. Use a `pydantic-settings` model that loads from a static file:

```ini
# src/config/event_flow.ini
[transition:draft->active]
allowed_roles = organizer, admin
checks = registration_open, min_players

[transition:active->cancelled]
allowed_roles = organizer
checks = none
```

```python
# src/env_config.py — optional sub-config
from pydantic_settings import BaseSettings
from src.config import path  # path to config file

class EventFlowConfig(BaseSettings):
    model_config = SettingsConfigDict(ini_file=path)

    # parse transitions into a dict or data class
    transitions: dict[str, TransitionRule] = {}

    @classmethod
    def load_from_ini(cls) -> "EventFlowConfig":
        return cls(_env_file=FLOW_INI_PATH)

class Env(LocalSettings):
    # …
    event_flow: EventFlowConfig | None = None  # optional — set only if the domain needs it
```

**When to use:**
- Domain has 5+ statuses with branching transition rules (not every `→` every is valid).
- Transition rules change per event type or per deployment without code changes.
- Otherwise, a simple enum + `if/ match` guard in the service is simpler and preferred.

**Conventions:**
- The config file lives in `src/config/` (not in `src/infra/` or `src/app/`) since it describes domain state machines, not infrastructure.
- Services load transition rules via the `env` singleton — no direct file reads in core.
- The `Env` field is `Optional` and explicitly `None` when the project doesn't use state machine configs.

## 11. Transport Layer (`src/app/`)

Pick one of the two below, or both if the project genuinely needs an HTTP surface and async messaging at the same time. Either way, they call into the exact same `src/core/services/*` and translate at the boundary using the external models from §6.

### 11a. FastAPI (HTTP)

```python
# src/app/http/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.env_config import env
from src.core.exceptions import DomainException
from src.infra.postgre.engine import DatabaseSessionManager
from src.app.http.api import router  # combined APIRouter from your route modules


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_manager = DatabaseSessionManager(env.postgres.url)
    app.state.session_manager = session_manager
    # optional, only if Redis is used:
    # redis_engine = RedisSessionManager(env.redis.url)
    # app.state.redis_engine = redis_engine
    yield
    await session_manager.close()
    # if using redis: await redis_engine.close()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc: DomainException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})
```

Entrypoint: `uvicorn src.app.http.main:app`

### 11b. FastStream (RabbitMQ)

```python
# src/app/rabbit/main.py
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from faststream import Context, ContextRepo, ExceptionMiddleware, FastStream
from faststream.rabbit import Channel, RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DomainException
from src.core.response import ErrorResponse, ResponseMessage
from src.env_config import env
from src.infra.postgre.engine import DatabaseSessionManager

exc_middleware = ExceptionMiddleware()
logger = logging.getLogger(__name__)


@exc_middleware.add_handler(DomainException, publish=True)
async def error_handler(
    exc: DomainException,
    db_session: Annotated[AsyncSession | None, Context("db_session", default=None)] = None,
) -> ResponseMessage[ErrorResponse]:
    if db_session is not None:
        await db_session.rollback()
    return ResponseMessage(status=exc.status_code, message=ErrorResponse(message=exc.message))


broker = RabbitBroker(
    env.rabbit.url,
    middlewares=[exc_middleware],
    default_channel=Channel(prefetch_count=10),
)

# Register route modules
# broker.include_router(api.router)


@asynccontextmanager
async def lifespan(context: ContextRepo):
    session_manager = DatabaseSessionManager(env.postgres.url)
    context.set_global("session_manager", session_manager)

    # optional, only if Redis is used:
    # redis_engine = RedisSessionManager(env.redis.url)
    # context.set_global("redis_engine", redis_engine)

    context.set_global("broker", broker)
    yield

    # if using redis: await redis_engine.close()
    await session_manager.close()


app = FastStream(broker, lifespan=lifespan)
```

Entrypoint: `python start.py` (see §16).

An **RPC client** over `aio_pika` (exclusive reply queues, semaphore-bounded concurrency, correlation-ID tracking, timeout handling) is only needed if a service must make synchronous request/response calls to another service over the broker. If pub/sub or fire-and-forget messaging is enough, skip it entirely.

### 11c. Running both together

Keep two separate app factories (`app/http/main.py`, `app/rabbit/main.py`) and two entrypoints/processes when both are needed — simplest to reason about and scale independently. If they must share a single process, start the FastStream broker from inside FastAPI's `lifespan` (`await broker.start()` / `await broker.close()`) instead of merging the two factories.

---

## 12. Database & Migrations

### Engine (`src/infra/postgre/engine.py`)

```python
class DatabaseSessionManager:
    def __init__(self, connect_string: str):
        self._engine = create_async_engine(connect_string, echo=False)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
```

### Alembic (`alembic/env.py`)

- **Async migrations** via `async_engine_from_config` + `asyncio.run()`.
- **URL injected** from `env.postgres.url` — not hardcoded in `alembic.ini`.
- **`NullPool`** — no connection pooling during migrations.
- **Single metadata source** — `target_metadata = Base.metadata`.

### ORM Conventions

- Table names: explicit `'entity_table'` string, not auto-generated.
- All models are `*Model` suffix (e.g., `EventModel`).
- `relationship(..., lazy="noload")` — no automatic lazy loading.
- All FKs use `ondelete='CASCADE'`.
- Status transitions (if the domain needs them) validated via a `transition_to()` method reading rules from config — optional.

---

## 13. Testing Strategy

### Layered Conftest

**`tests/conftest.py`** (session-scoped):
```python
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_engine(postgres_container: str) -> AsyncEngine:
    engine = create_async_engine(postgres_container, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine

@pytest_asyncio.fixture(loop_scope="session")
async def async_session(async_engine: AsyncEngine) -> AsyncSession:
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        sf = async_sessionmaker(conn, expire_on_commit=False,
                                join_transaction_mode="create_savepoint")
        async with sf() as session:
            yield session
        await trans.rollback()  # rollback per test
```

**`tests/repo/conftest.py`** — one fixture per repository + entity chain fixtures.
**`tests/services/conftest.py`** — repo fixtures + service fixtures + stub external clients.

### Pytest Config (`pytest.ini`)

```ini
[pytest]
asyncio_mode = auto
dotenv_load_dotenv = true
dotenv_file = .env
```

No `@pytest.mark.asyncio` needed — `asyncio_mode = auto` detects `async def test_*`. This layer is identical regardless of transport, since tests exercise repos/services directly and don't touch `src/app/`.

---

## 14. Key Conventions — Quick Reference

| Area | Convention |
|---|---|
| **Layering** | `app/` (entrypoints + external models) → `core/` (domain) ← `infra/` (driven adapters) |
| **Transport** | FastAPI routers and/or FastStream handlers, both under `src/app/` — inject the same DI aliases from `dependency.py` |
| **External contract** | Request/response/message schemas in `app/*/models/` — mapped to/from `core/commands` and `core/results` at the boundary |
| **Endpoint responses** | Always `response_model=<Schema>` (FastAPI) / typed `ResponseMessage[<Schema>]` (FastStream) with a concrete Pydantic model — never `dict`, `dict[str, Any]`, or omitted; see §6 and §15.11 |
| **Naming: domain DTOs** | Unsuffixed (`Event`, `EventCreate`, `EventUpdate`) — `src.core.models` |
| **Naming: ORM** | `*Model` suffix (`EventModel`) — `src.infra.postgre.models` |
| **Naming: Repo protocols** | `*RepositoryProtocol` — `src.core.interfaces.repo` |
| **Naming: Repo implementations** | `*Repository` — `src.infra.postgre.repo` |
| **Naming: Tables** | Explicit `'<entity>_table'` string |
| **Relationship loading** | `lazy="noload"` — opt-in via `selectinload()` in repo methods |
| **DTO→ORM mapping** | `dto_model.model_validate(obj, from_attributes=True)` |
| **ORM→DTO mapping** | `model_dump()` filtered to column names |
| **Integrity errors** | Caught in `_flush()`, re-raised as typed exceptions |
| **Config** | pydantic-settings `Env` singleton — `.url` properties; optional infra gets its own sub-config only if used |
| **DI** | `Depends` + `Annotated` type aliases in `src/dependency.py` — same aliases work for FastAPI and FastStream |
| **Error handling** | `DomainException` hierarchy — caught by FastAPI exception handler or FastStream `ExceptionMiddleware`, both in `app/` |
| **Migrations** | Async via `async_engine_from_config` + `NullPool` |
| **Testing** | testcontainers Postgres, session-scoped engine, transaction-rollback per test |
| **Entrypoint** | `start.py` → `uvicorn ...` (FastAPI) or `app.run()` (FastStream) |
| **Docker** | `entrypoint.sh` → `alembic upgrade head && python start.py` |
| **Store protocols** | `*StoreProtocol` in `core/interfaces/repo/`, implementation in `infra/redis/` — key-value with TTL; see §7d |
| **Client protocols** | `*Protocol` in `core/interfaces/clients/`, implementation in `infra/clients/` — external service calls; see §7e |
| **Permission/access** | Stateless functions in `core/interfaces/repo/access.py` — called from services; see §4a |

---

## 15. Anti-Patterns / Gotchas

1. **Don't import domain DTOs from ORM models.** `src.core.*` never imports `src.infra.*`.
2. **Don't skip `__init__.py` barrel exports.** New entities must be added to both `models/__init__.py` and `repo/__init__.py`.
3. **Don't use `lazy="select"` or `lazy="joined"` on relationships.** Default is `lazy="noload"`; every fetch is explicit via `selectinload()`.
4. **Don't put business logic in repos.** Repos map DTOs ↔ ORM and handle DB errors. Validation, authorization, and state machines belong in services.
5. **Don't hardcode connection strings.** Use `env.postgres.url` etc. — derive from env vars with local defaults.
6. **Don't forget `model_rebuild()`** after extending DTOs with new forward references.
7. **Don't use synchronous sessions.** Everything is `async def`.
8. **Don't let `src/core/` import `fastapi`, `faststream`, or anything from `src/app/` or `src/infra/`.** Only `src/app/*`, `src/infra/*`, and `src/dependency.py` should know which transport(s) are in play — that's what lets you add, drop, or swap FastAPI/FastStream without touching business logic.
9. **Don't put external request/response/message models in `core/`.** They belong in `app/*/models/` next to the listeners that use them, mapped explicitly to `core/commands` and `core/results` — see §6.
10. **Don't bring in Redis, RabbitMQ, or an RPC client "just in case."** Add each piece only when a concrete requirement needs it; unused infra is dead weight to maintain and test.
11. **Don't return `dict` or `dict[str, Any]` from an endpoint, and don't skip `response_model`.** Both break OpenAPI schema generation and response validation. If a proper response schema doesn't exist yet, write one — a Pydantic model in `app/*/models/` that mirrors the actual fields the service/repo returns. `dict[str, Any]` is not a looser version of a strict model, it's the absence of one; it does not satisfy this rule even when offered as a fix after a review comment.
12. **Don't put client protocols (external service calls, RPC, message publish) in `interfaces/repo/`.** They belong in `interfaces/clients/`. A protocol without a corresponding ORM table is likely a client or store protocol — see §7e and §7d.
13. **Don't use Redis as a primary database.** Stores are for ephemeral data with TTL. If data must survive a restart or be queried by anything other than key lookup, put it in Postgres via a Repository.
14. **Don't duplicate permission checks across services.** Keep access logic in a single `access.py` module per bounded context — see §4a. Duplicated checks inevitably diverge and create security holes.
15. **Don't let entrypoints import from `infra/` directly.** Handlers in `src/app/` should only import from `src.core.*`, `src.dependency`, and `src.core.response`. Infra details (engine, session, broker) are injected via DI — see §9.

---

## 16. Reusable Boilerplate

These modules are **fully generic** — copy them as-is into any async Python backend with this stack. Only import paths and env-var keys need adjustment. Sections marked *optional* should only be copied in if the project actually needs that piece.

### 16.1 `src/infra/postgre/engine.py` — Async Engine + Session Manager (mandatory)

```python
import contextlib
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection, AsyncSession,
    async_sessionmaker, create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DatabaseSessionManager:
    """Async SQLAlchemy engine + session lifecycle.

    Usage:
        session_manager = DatabaseSessionManager("postgresql+asyncpg://...")
        async with session_manager.session() as session:
            session.execute(...)   # auto-commits or rolls back
    """

    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None):
        engine_kwargs = engine_kwargs or {}
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False, bind=self._engine, expire_on_commit=False,
        )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    async def opened(self) -> bool:
        return self._engine is not None
```

### 16.2 `src/infra/redis/engine.py` — Redis Session Manager (*optional* — only if the project uses Redis)

```python
import contextlib
from typing import AsyncIterator

from redis.asyncio import Redis, ConnectionPool


class RedisSessionManager:
    """Async Redis connection-pool lifecycle.

    Usage:
        redis_engine = RedisSessionManager("redis://...")
        async with redis_engine.client() as redis:
            await redis.get("key")
    """

    def __init__(self, url: str):
        self._url = url
        self._pool: ConnectionPool | None = ConnectionPool.from_url(self._url)

    async def close(self):
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None

    async def reopen(self):
        if self._pool is None:
            self._pool = ConnectionPool.from_url(self._url)

    @contextlib.asynccontextmanager
    async def client(self) -> AsyncIterator[Redis]:
        if self._pool is None:
            self._pool = ConnectionPool.from_url(self._url)
        client = Redis(connection_pool=self._pool)
        try:
            yield client
        finally:
            await client.aclose()

    @property
    async def opened(self) -> bool:
        return self._pool is not None
```

### 16.3 `src/logging_setup.py` — Structured Logging

```python
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import traceback

LOG_FILE_PATH = Path('.local') / 'temp.log'

_DEF_FORMAT = '[%(asctime)s] %(levelname)s %(name)s:%(lineno)d %(message)s'
_DEF_DATEFMT = '%Y-%m-%d %H:%M:%S'

_configured = False


def _log_unhandled_exception(exc_type, exc_value, exc_tb):
    logger = logging.getLogger('UNCAUGHT')
    formatted_tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.error('Uncaught exception with traceback:\n%s', formatted_tb)


def setup_logging(level: int = logging.INFO):
    global _configured
    if _configured:
        return
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(_DEF_FORMAT, _DEF_DATEFMT)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    fh = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8',
    )
    fh.setLevel(level)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    sys.excepthook = _log_unhandled_exception
    logging.getLogger(__name__).info('Logging initialized. File=%s', LOG_FILE_PATH.resolve())
    _configured = True


__all__ = ['setup_logging', 'LOG_FILE_PATH']
```

### 16.4 `src/infra/postgre/repo/base.py` — Generic BaseRepository (mandatory)

```python
from typing import Any, Generic, Mapping, Sequence, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..engine import Base
from ..exceptions import IntegrityForeignException, IntegrityUniqueException, IntegrityUnknownException

ModelType = TypeVar("ModelType", bound=Base)
CreateDTO = TypeVar("CreateDTO", bound=BaseModel)
ReadDTO = TypeVar("ReadDTO", bound=BaseModel)
UpdateDTO = TypeVar("UpdateDTO", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateDTO, ReadDTO, UpdateDTO]):
    model: Type[ModelType]
    dto_model: Type[ReadDTO]

    def __init__(self, session: AsyncSession):
        self._session = session
        if not hasattr(self, "model"):
            raise NotImplementedError("Repository must define 'model' class attribute")
        if not hasattr(self, "dto_model"):
            raise NotImplementedError("Repository must define 'dto_model' class attribute")

    async def _flush(self) -> None:
        try:
            await self._session.flush()
        except IntegrityError as exc:
            sql_state = getattr(exc.orig, "sqlstate", None)
            if sql_state == "23503":
                raise IntegrityForeignException() from exc
            if sql_state == "23505":
                raise IntegrityUniqueException() from exc
            raise IntegrityUnknownException() from exc

    async def _get_model(self, field_id: UUID, options: list[Any] | None = None) -> ModelType | None:
        stmt = select(self.model).where(getattr(self.model, "id") == field_id)
        if options:
            stmt = stmt.options(*options)
        result = await self._session.scalar(stmt)
        return result

    def _to_dto(self, obj: Any) -> ReadDTO:
        return self.dto_model.model_validate(obj, from_attributes=True)

    async def _get(self, field_id: UUID, options: list[Any] | None = None) -> ReadDTO | None:
        obj = await self._get_model(field_id, options=options)
        return self._to_dto(obj) if obj else None

    async def get(self, field_id: UUID) -> ReadDTO | None:
        return await self._get(field_id)

    async def _list_model(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        if options:
            stmt = stmt.options(*options)
        if order_by is not None:
            stmt = stmt.order_by(order_by)

        result = await self._session.scalars(stmt)
        return result.all()

    async def get_list(
            self,
            offset: int = 0,
            limit: int | None = 100,
            options: list[Any] | None = None,
            *where_clauses: Any,
            order_by: Any = None,
    ) -> Sequence[ReadDTO]:
        items = await self._list_model(offset, limit, options, *where_clauses, order_by=order_by)
        return [self._to_dto(item) for item in items]

    def _dto_to_data(self, dto: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(dto, "model_dump"):
            raw_data = dto.model_dump(exclude_unset=exclude_unset)
        elif isinstance(dto, Mapping):
            raw_data = dict(dto)
        else:
            raw_data = dict(dto.__dict__)

        column_names = set(self.model.__mapper__.columns.keys())
        return {k: v for k, v in raw_data.items() if k in column_names}

    async def create(self, dto: CreateDTO) -> ReadDTO:
        create_data = self._dto_to_data(dto)
        obj = self.model(**create_data)
        self._session.add(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def update(self, dto: UpdateDTO) -> ReadDTO:
        update_data = self._dto_to_data(dto, exclude_unset=True)
        obj = self.model(**update_data)
        obj = await self._session.merge(obj)
        await self._flush()
        await self._session.refresh(obj)
        return self._to_dto(obj)

    async def delete(self, field_id: UUID) -> bool:
        obj = await self._get_model(field_id)
        if obj:
            await self._session.delete(obj)
            await self._flush()
            return True
        return False

    async def exists(self, field_id: UUID) -> bool:
        stmt = select(func.count()).select_from(self.model).where(getattr(self.model, "id") == field_id)
        count = await self._session.scalar(stmt)
        return (count or 0) > 0

    async def count(self, *where_clauses: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        if where_clauses:
            for clause in where_clauses:
                stmt = stmt.where(clause)
        val = await self._session.scalar(stmt)
        return val or 0
```

> **Protocol inheritance requirement:** concrete repositories MUST also inherit their entity-specific `*RepositoryProtocol`. The base class provides the implementation; the protocol provides the type-checkable contract. See §7c for the pattern.

### 16.5 `start.py` — Entrypoint

FastAPI variant:
```python
import logging
import uvicorn

from src.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    uvicorn.run("src.app.http.main:app", host="0.0.0.0", port=8000)
```

FastStream variant:
```python
import asyncio
import logging

from src.app.rabbit.main import app
from src.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    asyncio.run(app.run())
```

### 16.6 `entrypoint.sh` — Docker CMD

```sh
alembic upgrade head
python start.py
```

### 16.7 `Dockerfile` — Python + uv Build

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install --system --editable .

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "entrypoint.sh"]
```

### 16.8 `src/app/rabbit/main.py` — FastStream App Factory Template (*optional* — only if using RabbitMQ)

```python
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from faststream import Context, ContextRepo, ExceptionMiddleware, FastStream
from faststream.rabbit import Channel, RabbitBroker
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DomainException
from src.core.response import ErrorResponse, ResponseMessage
from src.env_config import env
from src.infra.postgre.engine import DatabaseSessionManager

exc_middleware = ExceptionMiddleware()
logger = logging.getLogger(__name__)


@exc_middleware.add_handler(DomainException, publish=True)
async def error_handler(
    exc: DomainException,
    db_session: Annotated[AsyncSession | None, Context("db_session", default=None)] = None,
) -> ResponseMessage[ErrorResponse]:
    if db_session is not None:
        await db_session.rollback()
    return ResponseMessage(status=exc.status_code, message=ErrorResponse(message=exc.message))


broker = RabbitBroker(
    env.rabbit.url,
    middlewares=[exc_middleware],
    default_channel=Channel(prefetch_count=10),
)

# Register route modules
# broker.include_router(api.router)


@asynccontextmanager
async def lifespan(context: ContextRepo):
    session_manager = DatabaseSessionManager(env.postgres.url)
    context.set_global("session_manager", session_manager)

    # optional, only if Redis is used:
    # redis_engine = RedisSessionManager(env.redis.url)
    # context.set_global("redis_engine", redis_engine)

    context.set_global("broker", broker)
    yield

    # if using redis: await redis_engine.close()
    await session_manager.close()


app = FastStream(broker, lifespan=lifespan)
```

**To adapt:** uncomment `broker.include_router(...)` and point it at your project's handler module(s) in `src/app/rabbit/api/`. The error middleware catches any `DomainException` thrown from handlers, rolls back the DB session, and returns a structured error response — no try/except needed in individual handlers.

### 16.9 `src/app/http/main.py` — FastAPI App Factory Template (*optional* — only if exposing HTTP)

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.core.exceptions import DomainException
from src.env_config import env
from src.infra.postgre.engine import DatabaseSessionManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_manager = DatabaseSessionManager(env.postgres.url)
    app.state.session_manager = session_manager

    # optional, only if Redis is used:
    # redis_engine = RedisSessionManager(env.redis.url)
    # app.state.redis_engine = redis_engine

    yield

    # if using redis: await redis_engine.close()
    await session_manager.close()


app = FastAPI(lifespan=lifespan)

# Register route modules
# from src.app.http.api import router
# app.include_router(router)


@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc: DomainException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message})
```

**To adapt:** uncomment the router import/include and point it at your project's endpoint modules in `src/app/http/api/`. The exception handler catches any `DomainException` thrown from endpoints and returns a structured error response — same contract as the FastStream variant in §16.8.
