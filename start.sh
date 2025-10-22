#!/usr/bin/env bash
set -euo pipefail

cd /app

# If a command was provided, run it.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

# Try common entry scripts
if [ -f "main.py" ]; then
  exec python -u main.py
elif [ -f "app.py" ]; then
  exec python -u app.py
elif [ -f "extract.py" ]; then
  exec python -u extract.py
else
  echo "No entry script found (main.py/app.py/extract.py)."
  echo "Pass a command to run, e.g.: docker run --rm <image> python your_script.py"
  exec bash
fi
