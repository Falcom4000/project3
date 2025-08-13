BASE_DIR=$(dirname "$0")
LOG_DIR="$BASE_DIR/logs"
SERVER_LOG="$LOG_DIR/server.log"
REDIS_LOG="$LOG_DIR/redis_stdout.log"
echo "Starting server in the background (logs at $SERVER_LOG)..."
# Redirect server's stdout and stderr to a log file
python "$BASE_DIR/server/server.py" > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
trap "echo 'Shutting down server...'; kill $SERVER_PID; echo 'Stopping Redis Stack...'; sudo killall -q redis-stack-server || true" EXIT

# Give the server a few seconds to initialize
echo "Waiting for server to start..."
sleep 3

echo "Starting client..."
# The client runs in the foreground and now has exclusive control of the terminal
python "$BASE_DIR/client/client.py"

echo "Client has exited."