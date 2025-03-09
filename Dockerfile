FROM python:3.11-slim

RUN apt update && apt install -y libpq-dev gcc

RUN pip install poetry==1.6.1

RUN poetry config virtualenvs.create false

WORKDIR /code

COPY ./pyproject.toml ./README.md ./poetry.lock* ./

COPY ./package[s] ./packages

COPY ./source_docs ./source_docs

RUN poetry install  --no-interaction --no-ansi --no-root

COPY ./app ./app

RUN poetry install --no-interaction --no-ansi

# Also install from requirements.txt to ensure all dependencies are available
COPY ./requirements.txt ./
RUN pip install -r requirements.txt

# Expose port 8000 for Elastic Beanstalk
EXPOSE 8000

# Use port 8000 explicitly for Elastic Beanstalk
CMD exec uvicorn app.server:app --host 0.0.0.0 --port 8000
