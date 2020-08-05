FROM python:3.8-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/venv

RUN apt-get update && apt-get install -y curl make \
 && curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* \
 && python -m venv $VIRTUAL_ENV

ENV PATH=$VIRTUAL_ENV/bin:/root/.poetry/bin:$PATH

COPY pyproject.toml poetry.lock* ./
RUN poetry install -n --no-dev \
 && rm -rf /root/.cache/pip

COPY . .
RUN poetry install -n --no-dev

ENTRYPOINT [ "poetry", "run", "kongcli" ]
