#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "\033[1;31mError: .env file not found at $ENV_FILE\033[0m" >&2
    exit 1
fi

# This automatically exports all variables that are defined or modified
# from this point on.
set -o allexport
# Source the .env file. This reads it and defines the variables.
# The '|| true' is a safeguard in case the file is empty.
source "$ENV_FILE" || true
set +o allexport

echo "✅ Environment loaded." # Optional: for debugging
