#!/bin/bash

# this file's purpose is to run the seed file before the launch of the fastapi server, and thus avoid inefficiencies with grouping `lifespan` and seed.
# echo "Waiting for Neo4j (bolt://neo4j:7687) to wake up..."

# while ! nc -z neo4j 7687; do
#   echo "Neo4j is still sleeping... retrying in 1s"
#   sleep 1
# done

# echo "Neo4j is UP. Ready to seed and boot."
set -e  # aka. errExit; exit immediately if a command exits with a non-zero status

echo -e "Starting backend boot..."  # print, in account of backspaced chars

# 1st, run seed before starting fastapi server
echo "Executing seed.py..."
python ./infra/seed.py  
echo "COMPLETED: seed.py"

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
echo "COMPLETED: FastAPI server start"
