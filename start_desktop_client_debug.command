#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec mac/start_desktop_client_debug.command
