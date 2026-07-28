# AccessDataRequest

**File:** `src/app/rabbit/models/base.py`

Блок авторизации, встраиваемый в защищённые запросы. Передаётся в каждом request к защищённым очередям RabbitMQ.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `member_id` | `UUID \| None` | ID участника, выполняющего запрос. `None` для анонимных запросов |
| `server_id` | `UUID` | ID сервера, к которому относится запрос |
| `permission_mask` | `int` | Битовоя маска прав участника (см. [_shared/permission-bits.md](permission-bits.md)) |
| `restriction_mask` | `int` | Битовоя маска ограничений участника |

## Usage

`AccessDataRequest` включено как поле `access_data` во все защищённые Command-схемы. Сервисы используют его для проверки прав через `PERMISSION.check_permission()` и ограничений через `RESTRICTION.check_restriction()`.

## See Also

- [_shared/permission-bits.md](permission-bits.md) — формат битовой маски прав
- [_shared/enums.md](enums.md) — RESTRICTION enum
