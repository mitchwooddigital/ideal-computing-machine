#!/bin/bash
# Runs the morning brief headless through the Claude Code CLI.
# Called by launchd at 7am (see install.sh). Safe to run by hand to test.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$HOME/Library/Logs/luxbmx-morning-brief.log"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  claude -p "$(cat "$DIR/prompt.md")" --permission-mode auto --output-format text
  echo
} >> "$LOG" 2>&1
