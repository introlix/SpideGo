#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SEARXNG_SETTINGS_PATH="$SCRIPT_DIR/settings.yml"
export PYTHONPATH="$SCRIPT_DIR/searxng"

exec python3 -m searx.webapp