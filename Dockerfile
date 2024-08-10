FROM python:3.10-slim

ENV \
  PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  POETRY_HOME="/opt/poetry" \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_VERSION="1.8.3" \
  POETRY_NO_INTERACTION=1 \
  PYSETUP_PATH="/opt/service" \
  VENV_PATH="/opt/service/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

RUN pip install poetry

WORKDIR /src

COPY app/pyproject.toml app/poetry.lock /src/app/

RUN poetry --directory app install

COPY app/app /src/app/app
COPY data /src/data

EXPOSE 8501

CMD ["poetry", "--directory", "app", "run", "streamlit", "run", "app/app/main.py"]
