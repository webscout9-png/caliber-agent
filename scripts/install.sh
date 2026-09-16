#!/usr/bin/env bash
set -euo pipefail

echo "Installing Caliber Agent..."

if command -v pipx >/dev/null 2>&1; then
  pipx install --force git+https://github.com/webscout9-png/caliber-agent.git
elif command -v pip3 >/dev/null 2>&1; then
  pip3 install --user --upgrade git+https://github.com/webscout9-png/caliber-agent.git
elif command -v pip >/dev/null 2>&1; then
  pip install --user --upgrade git+https://github.com/webscout9-png/caliber-agent.git
else
  echo "Error: need pip or pipx (Python 3.10+)"
  exit 1
fi

echo ""
echo "Done. Run:  caliberagent"
echo "Then:       /provider <openrouter-key>"
echo ""
