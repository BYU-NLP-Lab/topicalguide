#!/bin/bash

# Stop the Django development server

echo "Looking for Django server processes..."

# Find Django server processes
PIDS=$(ps aux | grep "manage.py runserver" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No Django server processes found."
    exit 0
fi

echo "Found Django server process(es): $PIDS"
echo "Stopping server..."

# Kill the processes
for PID in $PIDS; do
    kill $PID
    echo "Sent SIGTERM to process $PID"
done

# Wait a moment and check if they're gone
sleep 2

# Check if any are still running
REMAINING=$(ps aux | grep "manage.py runserver" | grep -v grep | awk '{print $2}')

if [ -z "$REMAINING" ]; then
    echo "Server stopped successfully."
else
    echo "Some processes still running, forcing kill..."
    for PID in $REMAINING; do
        kill -9 $PID
        echo "Sent SIGKILL to process $PID"
    done
    echo "Server forcefully stopped."
fi
