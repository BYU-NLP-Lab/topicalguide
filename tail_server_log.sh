#!/bin/bash

# Tail the Django server log

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Use the symlink to the latest log file
LOG_FILE="$SCRIPT_DIR/logs/server-latest.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "Latest log file not found: $LOG_FILE"
    echo "Start the server first with: ./start_server.sh"
    echo ""
    echo "Available log files:"
    ls -lt "$SCRIPT_DIR/logs"/server-*.log 2>/dev/null | head -5
    exit 1
fi

# Resolve the symlink to show the actual file being tailed
ACTUAL_LOG=$(readlink "$LOG_FILE")

echo "Tailing server log: logs/$ACTUAL_LOG"
echo "Press CTRL-C to stop tailing"
echo ""

tail -f "$LOG_FILE"
