#!/bin/bash

# this file's purpose is to run the seed file before the launch of the fastapi server, and thus avoid inefficiencies with grouping `lifespan` and seed.

set -e  # aka. errExit; exit immediately if a command exits with a non-zero status

echo -e "Starting backend boot..."  # print, in account of backspaced chars

# 1st, run seed before starting fastapi server
echo "Executing `seed.py`"
python /backend/infra/seed.py  

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
