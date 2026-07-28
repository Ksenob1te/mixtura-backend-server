# BaseRepository

**Protocol:** Generic CRUD (inherited by all repositories)
**Implementation:** `src/infra/postgre/repo/base.py`

Generic CRUD providing standard `get` and `delete` operations. All repository implementations inherit from `BaseRepositoryImpl[ModelT]` and implement the corresponding `*RepositoryProtocol`.

## Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get` | `(id: UUID, /) -> ModelT \| None` | Get by primary key using `SELECT … WHERE id = :id LIMIT 1` |
| `delete` | `(id: UUID, /) -> bool` | Delete by primary key using `DELETE … WHERE id = :id`. Returns `True` if a row was deleted |

## Notes

- Both methods are inherited by all 14 repository implementations
- Custom repositories may override `get` to add eager loading or override `delete` for custom delete logic
- All methods use `AsyncSession` and assume a transaction context managed by the caller
- Integrity errors from the database layer are caught and wrapped in `RepositoryException` subclasses
