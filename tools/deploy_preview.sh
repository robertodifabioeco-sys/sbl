#!/usr/bin/env bash
# Pubblica l'anteprima su https://robertodifabioeco-sys.github.io/sbl/ (ramo gh-pages del repo sbl).
set -euo pipefail
cd "$(dirname "$0")/.."
python tools/build.py --preview
python tools/check_links.py >/dev/null || true
TMP=$(mktemp -d)
cp -r dist-preview/. "$TMP"/
cd "$TMP"
git init -q -b gh-pages
git add -A
git commit -q -m "Anteprima sito SBL $(date +%Y-%m-%d\ %H:%M)"
git push -q -f https://github.com/robertodifabioeco-sys/sbl.git gh-pages
cd - >/dev/null
rm -rf "$TMP"
echo "Pubblicato: https://robertodifabioeco-sys.github.io/sbl/"
