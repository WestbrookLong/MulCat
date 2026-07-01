#!/bin/bash
cd "$(dirname "$0")/.." || exit 1

if [ -x ".venv/bin/python" ] && [ -z "${PYTHON_BIN}" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi
"${PYTHON_BIN}" -m mac.main > mulcat-start.log 2>&1
status=$?

if [ "${status}" -ne 0 ]; then
  echo "MulCat exited with code ${status}. See mulcat-start.log for details."
  echo "Press Return to close this window..."
  read -r _
fi

exit "${status}"

