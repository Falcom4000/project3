#!/bin/bash

# Get the directory where the script is located to ensure paths are correct
BASE_DIR=$(dirname "$0")

# Activate virtual environment if it exists
# if [ -f "$BASE_DIR/venv/bin/activate" ]; then
#   source "$BASE_DIR/venv/bin/activate"
# fi

echo "Starting server in the background..."
python3 "$BASE_DIR/server/server.py" &
SERVER_PID=$!

# Add a trap to kill the server process when the script exits
trap "echo 'Shutting down server...'; kill $SERVER_PID" EXIT

# Give the server a few seconds to initialize
echo "Waiting for server to start..."
sleep 3

echo "Starting client..."
python3 "$BASE_DIR/client/client.py"

echo "Client has exited."
