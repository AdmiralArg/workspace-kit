#!/bin/sh
# Runs a hook script with a Python that actually works on this machine.
#
#   sh run.sh /path/to/hook.py
#
# On Windows `python3` is often a shortcut to the Store that runs nothing, so each
# candidate is tried before it is used. Called through `sh`, so it does not need
# the executable bit, which is lost when a folder is synced between machines.
# With no working Python it exits 0 in silence: a hook must never fail a session.
# The app sends and reads UTF-8. On Windows, Python would otherwise use the old
# Windows encoding and misread every character outside plain English.
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
script="$1"
shift
for py in python3 python py; do
  if "$py" -c "import sys" >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done
exit 0
