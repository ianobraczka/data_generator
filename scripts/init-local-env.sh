#!/usr/bin/env sh
# Create a local, gitignored `.env` from the tracked template (safe for fresh clones).
set -e
ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
EXAMPLE="${ROOT_DIR}/.env.example"
TARGET="${ROOT_DIR}/.env"

if [ ! -f "$EXAMPLE" ]; then
  echo "init-local-env: missing ${EXAMPLE}" >&2
  exit 1
fi

if [ -f "$TARGET" ]; then
  echo "init-local-env: ${TARGET} already exists — not overwriting."
  echo "  Edit that file to set GEMINI_API_KEY and/or OPENAI_API_KEY, or delete it and run this script again."
  exit 0
fi

cp "$EXAMPLE" "$TARGET"
echo "init-local-env: created ${TARGET}"
echo "  Open it and set GEMINI_API_KEY (default provider) and/or OPENAI_API_KEY."
echo "  For AI schema commands, also install: pip install -r requirements-ai.txt"
echo "  Then: pip install -r requirements.txt"
echo "  Run CLI from the repo root (or any cwd under it) so python-dotenv can find .env."
