alembic upgrade head
python -m src.infra.postrge.static
python start.py