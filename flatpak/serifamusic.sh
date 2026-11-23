#!/bin/sh

cd /app/share/serifamusic || exit 1

export PYTHONPATH="/app/share/serifamusic/app${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

exec python3 /app/share/serifamusic/app/main.py "$@"
