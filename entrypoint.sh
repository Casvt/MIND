#!/usr/bin/env bash

set -e

PUID=${PUID:-0}
PGID=${PGID:-0}

DB_DIR="/app/db"
LOG_DIR="/app/logs"

if [ "$PUID" = "0" ]
then
    # Stay as root user
    echo "Running as root"
    exec "$@"

else
    # Switch to non-root user
    echo "Preparing MIND to run as $PUID:$PGID..."

    groupmod -o -g "$PGID" mind
    usermod -o -u "$PUID" -g "$PGID" mind

    echo "Ensuring ownership..."
    chown -R mind:mind "$DB_DIR" "$LOG_DIR" || {
        echo "Failed to update ownership to $PUID:$PGID"
        exit 1
    }

    echo "Running as $PUID:$PGID"
    exec gosu mind "$@"
fi
