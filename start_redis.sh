#!/bin/bash

# Get the directory where the script is located to ensure paths are correct
BASE_DIR=$(dirname "$0")
LOG_DIR="$BASE_DIR/logs"
SERVER_LOG="$LOG_DIR/server_stdout.log"
REDIS_LOG="$LOG_DIR/redis_stdout.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# --- Redis Stack Setup ---
# 1. Forcefully stop any old redis instances to ensure a clean slate.
echo "Stopping any lingering Redis processes..."
sudo killall -q redis-server redis-stack-server || true
sleep 1

# 2. Start the Redis Stack server, redirecting its output to a log file.
echo "Starting Redis Stack server (logs at $REDIS_LOG)..."
sudo redis-stack-server > "$REDIS_LOG" 2>&1 &