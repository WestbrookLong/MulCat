#!/bin/bash
cd "$(dirname "$0")" || exit 1

PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" desktop_client.py > mulcat-start.log 2>&1
status=$?

if [ "${status}" -ne 0 ]; then
  echo "MulCat exited with code ${status}. See mulcat-start.log for details."
  echo "Press Return to close this window..."
  read -r _
fi

exit "${status}"
