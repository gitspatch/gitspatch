FROM node:slim AS build-js

WORKDIR /build

COPY package.json package.json
COPY package-lock.json package-lock.json
COPY tailwind.config.js tailwind.config.js
COPY gitspatch gitspatch

RUN npm ci && npm run build

# ---

FROM python:3.12-slim AS build-python

RUN pip install -U pip hatch

WORKDIR /build

COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY LICENSE.md LICENSE.md
COPY gitspatch gitspatch
COPY --from=build-js /build/gitspatch/static gitspatch/static

RUN hatch build

# ---

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=build-python /build/dist/gitspatch-*.whl .

RUN pip install /app/gitspatch*.whl

ENV PORT=8000
ENV UVICORN_PORT=${PORT}
EXPOSE ${PORT}

CMD ["uvicorn", "gitspatch.main:app", "--host", "0.0.0.0"]