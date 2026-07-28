# PaginationRequest

**File:** `src/app/rabbit/models/base.py`

Стандартный запрос пагинации для list-операций.

## Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `page` | `int \| None` | No | `1` | Номер страницы (1-based) |
| `page_size` | `int` | No | `50` | Количество элементов на странице |

## Usage

`PaginationRequest` используется как базовый класс для list-команд или включается как поле в команды, требующие пагинации.
