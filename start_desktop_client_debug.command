#!/bin/bash
cd "$(dirname "$0")" || exit 1

unset MULCAT_UI_DEV_URL
PYTHON_BIN="${PYTHON_BIN:-python3}"
"${PYTHON_BIN}" desktop_client.py
status=$?

echo
echo "MulCat exited with code ${status}."
echo "Press Return to close this window..."
read -r _

exit "${status}"
