#!/bin/bash
# Publish audit data to gh-pages branch
# Used by GitHub Actions after audit completes

set -e

DATA_DIR="${1:-audit-data}"
BRANCH="gh-pages"

echo "Publishing audit data from $DATA_DIR to $BRANCH..."

# Check if data exists
if [ ! -d "$DATA_DIR" ]; then
  echo "Error: Data directory $DATA_DIR not found"
  exit 1
fi

# List generated files
echo "Files to publish:"
ls -la "$DATA_DIR"/*.json 2>/dev/null || echo "No JSON files found"

echo "Done. Data will be deployed by the GitHub Actions workflow."
