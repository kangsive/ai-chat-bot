#!/bin/bash

# Find the process using port 8000
PID=$(lsof -ti:8000)

if [ -n "$PID" ]; then
    echo "Killing uvicorn process with PID: $PID"
    kill -9 $PID
    echo "Process killed"
else
    echo "No process found running on port 8000"
fi

# Restart uvicorn - adjust the command based on your project setup
echo "Starting uvicorn server..."
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
uvicorn app.main:app --reload --port 8000
echo "Uvicorn restarted with PID: $!" 