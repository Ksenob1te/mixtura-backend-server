FROM python:3.13-slim

WORKDIR /mixtura-auth

COPY pyproject.toml ./

RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install --system --editable .

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "entrypoint.sh"]