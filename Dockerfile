FROM python:3.10-buster

WORKDIR /app

RUN pip install poetry

CMD pip install psycopg2-binary

COPY pyproject.toml poetry.lock ./

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.path /app/venv \
    && poetry install --no-root

COPY . /app

RUN chmod +x /app/start.sh

EXPOSE 8443

CMD ["/app/start.sh"]