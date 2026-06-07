FROM python:3.11-slim

WORKDIR /app

# Install system deps (kept minimal)
RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock* /app/poetry.lock

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY app /app/app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

