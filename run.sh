#!/bin/bash

set -e

alembic upgrade head
uvicorn gitspatch.main:app --host 0.0.0.0
