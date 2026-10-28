#!/usr/bin/env bash
set -euo pipefail

REPO="samyafk/VeloToulouseAnalytics"
DEST="../data/raw"

mkdir -p "$DEST"

echo "Downloading snapshots"

gh api --paginate "repos/$REPO/releases?per_page=100" --jq '.[].tag_name' |
while read -r tag; do
  echo "Checking $tag"
  gh release download "$tag" \
    --repo "$REPO" \
    --pattern "*.parquet" \
    --dir "$DEST" \
    --skip-existing
done