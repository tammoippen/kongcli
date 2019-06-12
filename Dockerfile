FROM python:3.6-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/venv

RUN apk add --no-cache curl \
 && curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python \
 && apk del --no-cache curl \
 && python -m venv $VIRTUAL_ENV

ENV PATH=$VIRTUAL_ENV/bin:/root/.poetry/bin:$PATH

COPY pyproject.toml ./
RUN poetry install -n --no-dev \
 && rm -rf /root/.cache/pip

RUN poetry install -n --no-dev \
 && rm -rf /root/.cache/pip

COPY . .
RUN poetry install -n --no-dev

ENTRYPOINT [ "poetry", "run", "kongcli" ]
