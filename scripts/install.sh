#!/usr/bin/env bash
set -euo pipefail

echo "Installing Caliber Agent..."

# Prefer pipx if available, else pip
if command -v pipx >/dev/null 2>&1; then
  pipx install git+https://github.com/webscout9-png/caliber-agent.git
elif command -v pip3 >/dev/null 2>&1; then
  pip3 install --user git+https://github.com/webscout9-png/caliber-agent.git
elif command -v pip >/dev/null 2>&1; then
  pip install --user git+https://github.com/webscout9-png/caliber-agent.git
else
  echo "Error: pip or pipx not found. Install Python 3.10+ first."
  exit 1
fi

echo ""
echo "✓ Caliber Agent installed."
echo "  Run:  caliberagent"
echo "  Then: /provider   (to add your OpenRouter API key)"
echo ""
