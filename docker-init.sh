#!/bin/sh

# WARNING: This file is for docker. DON'T execute directly.

set -e

# Upgrade database
alembic upgrade head

# Start server
uvicorn metasking:app --host 0.0.0.0 --port 80 --log-config log.conf
