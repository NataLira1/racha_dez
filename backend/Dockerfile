FROM python:3.10-slim AS builder

RUN apt update && \
    apt install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev

RUN curl -sSl https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml .

RUN poetry self add poetry-plugin-export

RUN poetry export -f requirements.txt --output requirements.txt

FROM python:3.10-slim AS runner

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app",  "--host", "0.0.0.0", "--port", "8000"]
