#!/bin/bash
# Installs (or reinstalls) the 7am launchd job for the morning brief.
# Run once: bash life/morning-brief/install.sh
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.luxbmx.morning-brief"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
chmod +x "$DIR/run.sh"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
launchctl unload "$PLIST" 2>/dev/null || true
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$DIR/run.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/luxbmx-morning-brief.launchd.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/luxbmx-morning-brief.launchd.log</string>
</dict>
</plist>
PL
launchctl load "$PLIST"
echo "Installed $LABEL. Fires daily at 7:00 local time."
echo "Test now:   bash $DIR/run.sh && tail -20 ~/Library/Logs/luxbmx-morning-brief.log"
echo "Remove:     launchctl unload $PLIST && rm $PLIST"
