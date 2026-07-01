#!/bin/bash
cd "$(dirname "$0")/.." || exit 1

unset MULCAT_UI_DEV_URL
if [ -x ".venv/bin/python" ] && [ -z "${PYTHON_BIN}" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi
"${PYTHON_BIN}" -m mac.main
status=$?

echo
echo "MulCat exited with code ${status}."
echo "Press Return to close this window..."
read -r _

exit "${status}"

