#!/bin/bash

LOCKFILE="/tmp/deploy.lock"

# Check if the lock file exists
if [ -e "$LOCKFILE" ]; then
    echo "Script is already running. Exiting."
    exit 1
fi

# Create a lock file
trap "rm -f $LOCKFILE; exit" INT TERM EXIT
touch "$LOCKFILE"

git pull
export STATIC_VERSION=`git rev-parse --short HEAD`
docker compose --profile $1 build
docker compose --profile $1 up -d

# Remove the lock file
rm -f "$LOCKFILE"
trap - INT TERM EXIT
