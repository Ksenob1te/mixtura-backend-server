# server-service — Agent Instructions

## Commands

```
uv run python start.py                    # Run app (requires RabbitMQ, Postgres, Redis)
uv run alembic upgrade head              # Apply migrations
uv run alembic revision -m "msg"         # Create migration
uv run python -m src.infra.postgre.static # Seed static data (permissions, restrictions)
docker compose -f docker-compose.dev.yaml up -d  # Start Postgres + Redis
uv run pytest                            # Run tests (requires Docker for Postgres testcontainers)
uv run pytest tests/repo                 # Repository tests only
uv run pytest tests/domain/service       # Service tests only
uv run pyright src                        # Type checking (static analysis)
uv run ruff check src                     # Linting (code style & errors)
```

Use `uv run` for Python commands.

Requires `.env` (copy from `.env.example`). Env loaded via `pydantic-settings` in `src/env_config.py`.

## Architecture

**Message-driven microservice** — FastStream + RabbitMQ, no HTTP. Each queue maps to one service method.

```
src/
  core/
    commands/       # Input DTOs (Pydantic Command)
    models/         # Domain DTOs (Read/Create/Update triplets, colocated enums)
    results/        # Output DTOs
    exceptions.py   # DomainException hierarchy
    services/       # Business logic classes (all scenarios)
    interfaces/
      repo/         # Repository protocols (typing.Protocol)
  app/
    rabbit/
      main.py       # FastStream app, broker, lifespan, error middleware
      api/          # Queue handlers — inject service via Depends
      models/       # External message schemas (wire contract)
  infra/
    postgre/        # SQLAlchemy ORM models + repo implementations + static seeding
    redis/          # Redis session manager + RedisRepository (cookie cache)
  dependency.py     # DI wiring (FastStream Depends + Context)
  env_config.py     # Env singleton (pydantic-settings)
  logging_setup.py  # Rotating file + console logging

**Key pattern:** API handlers call `service.method(data)` directly. No usecase layer. All services in `src/core/services/` receive repository protocols in `__init__`.

Flow: `api -|commands/results|> services -|repos|> orm models`.

**Four-file mirror per entity:**
| Layer | Path | Example |
|-------|------|---------|
| DTO | `src/core/models/<entity>.py` | `Server`, `ServerCreate`, `ServerUpdate` |
| Protocol | `src/core/interfaces/repo/<entity>.py` | `ServerRepositoryProtocol` |
| ORM Model | `src/infra/postgre/models/<entity>.py` | `Server` (DeclarativeBase) |
| Repo Impl | `src/infra/postgre/repo/<entity>.py` | `ServerRepository(BaseRepositoryImpl[Server])` |

## Important Conventions

- **Documentation:** When making code changes, you MUST update `docs/INDEX.md` and the corresponding documentation files. For looking up methods, services, repositories, and APIs, start by reading `docs/INDEX.md` and only load files for the relevant module — do not load the entire documentation tree. Use source code only for clarifying implementation details. Doc structure is defined in `docs/guides/structure.md`.
- **Auth/perms:** Bitmask-based permissions via `PERMISSION` enum (`src/infra/postgre/static/permissions.py`). Services call `PERMISSION.check_permission(mask, permission)` to guard operations. Restriction masks via `RESTRICTION` enum similarly.
- **Transactions:** One `AsyncSession` per message via `Depends(get_db_session)`. Commit on success, rollback on exception. `DomainException` triggers rollback in middleware (`main.py`) and returns `ResponseMessage(status=exc.status_code, message=ErrorResponse(message=exc.message))`.
- **Response envelope:** All handlers return `ResponseMessage[T]` with `status: int` and `message: T`. Success = status 200.
- **Repositories:** Protocol in `core/interfaces/repo/`, implementation in `infra/postgre/repo/`. `BaseRepositoryImpl[ModelT]` provides generic `get(id)` and `delete(id)`. Each repo impl inherits from both `BaseRepositoryImpl` and the corresponding protocol.
- **Repository tests:** Run only when repository protocols, implementations, or ORM mappings change.
- **ORM models:** Re-exported from `src/infra/postgre/models/__init__.py`. Domain DTOs use `from_attributes=True` for ORM-mode validation.
- **Static data seeding:** `python -m src.infra.postgre.static` runs before app start in Docker (`entrypoint.sh`). Seeds `PERMISSION` and `RESTRICTION` enum values into DB.
- **Alembic:** DB URL comes from `env.postgres.url` in `alembic/env.py`, not `alembic.ini`.
- **Redis:** Currently only used for `RedisRepository.get_user_by_cookie(cookie)`. Available for caching if needed.
- **Backward compatibility is NOT required.** All services are deployed atomically as a single unit. Wire formats (queue message schemas, DTOs, enums, bitmask values) can be changed freely without migration shims or deprecation periods. Prefer deletion over deprecation when removing code.
- **Architecture guide:** If you encounter a reusable solution pattern or a recurring anti-pattern worth documenting, **propose it to the user** for addition to `docs/guides/architecture-guide.md`. Don't add entries unilaterally — the user decides what goes into the guide. Keep the guide — not this file — as the living record of architectural decisions and conventions.

## Services (src/core/services/)

Services contain business scenarios and coordinate validation, permissions, repository calls, and external state. Services never import from `src/app/` or `src/infra/` (except ORM models for type convenience). Keep API handlers thin and persistence logic in repositories.

Update this table whenever adding, removing, or renaming services or service methods.

| Service | Functional area | Methods |
|---------|-----------------|---------|
| `CoreService` | Server CRUD, global template/reference data lookups | get_global_role_templates, get_global_rating_templates, get_global_permissions, get_global_restrictions, get_global_games, list_servers, list_user_servers, create_server, get_server, update_server, delete_server, delete_server_banner, delete_server_icon |
| `MemberService` | Member lifecycle, role assignment, membership management | list_members, join_server, create_virtual, get_member, update_member, kick_member, migrate_member |
| `AccessControlService` | Permission/restriction queries, restriction management | get_member, get_permissions, get_permission_mask, get_restrictions, get_restriction_mask, add_restriction, remove_restriction |
| `GameService` | Game CRUD, game-to-server management | get_all, add_to_server, remove_from_server |
| `GameRoleService` | Game role CRUD, global template copying | get, create, update, delete, reorder, copy_global_role_set |
| `RatingService` | Rating CRUD, global template copying | get, create, update, delete, reorder, copy_global_rating_set |
| `RoleService` | Server role CRUD, position reindexing | create, update, delete, reindex |
| `InviteService` | Invite creation, validation, usage tracking | create, list, delete, use_invite, generate_invite_code |
| `MemberCustomService` | Custom rating list management for members | get, add, update_rating, remove |

## Quirks

- Python 3.13+ required (`pyproject.toml`).
- `pytest.ini` loads `.env`, sets `asyncio_mode = auto`, and uses session-scoped asyncio loops; no `@pytest.mark.asyncio` needed.
- `tests/conftest.py` provides session-scoped `postgres_container`, `async_engine`, `async_session`, `helpers`, and `factory` (ServiceFactory for assembling repos+services).
- Domain models (`src/core/models/`) use Pydantic v2 with `from_attributes=True`, `frozen=True` for read models.
- ORM models use SQLAlchemy `DeclarativeBase` (`Base` from `engine.py`).
- Static enums (`PERMISSION`, `RESTRICTION`) are `StrEnum` with bitmask serialize/deserialize/check helpers. They exist both as Python enums and as seeded DB rows.
- Services often use `@staticmethod` for permission check helpers (e.g., `_can_manipulate_roles`, `_compute_overwrites_enum`).
- No HTTP layer — all communication is over RabbitMQ queues.
