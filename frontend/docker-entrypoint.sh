#!/bin/sh
set -e

# Safely configure runtime backend proxy URL from immutable template
if [ -f /app/configure-runtime.js ]; then
  node /app/configure-runtime.js
fi

exec "$@"
