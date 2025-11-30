#!/bin/bash

# Start Django development server with logging
# All output goes to logs/server-YYYY-MM-DD_HH-MM-SS.log

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Generate timestamp for log file name
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="$SCRIPT_DIR/logs/server-$TIMESTAMP.log"

# Create a symlink to the latest log file for easy access
LATEST_LINK="$SCRIPT_DIR/logs/server-latest.log"
ln -sf "server-$TIMESTAMP.log" "$LATEST_LINK"

# Store PID file
PID_FILE="$SCRIPT_DIR/logs/server.pid"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Server is already running (PID: $OLD_PID)"
        echo "Stop it first with: ./stop_server.sh"
        exit 1
    else
        # Stale PID file, remove it
        rm "$PID_FILE"
    fi
fi

# Print startup message
echo "========================================"
echo "Starting Django server at $(date)"
echo "Log file: $LOG_FILE"
echo "========================================"
echo ""

# Write startup message to log
cat >> "$LOG_FILE" << EOF
========================================
Starting Django server at $(date)
Log file: $LOG_FILE
========================================

EOF

# Start the server in the background and log all output
cd "$SCRIPT_DIR"
nohup venv/bin/python manage.py runserver >> "$LOG_FILE" 2>&1 &

# Save the PID
SERVER_PID=$!
echo $SERVER_PID > "$PID_FILE"

# Wait a moment for server to start
sleep 2

# Check if it's running
if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo "✓ Server started successfully (PID: $SERVER_PID)"
    echo ""
    echo "Tail the log with:"
    echo "  ./tail_server_log.sh"
    echo "  or"
    echo "  tail -f logs/server-latest.log"
    echo ""
    echo "Stop the server with:"
    echo "  ./stop_server.sh"
else
    echo "✗ Server failed to start. Check the log:"
    echo "  tail logs/server-latest.log"
    rm "$PID_FILE"
    exit 1
fi
