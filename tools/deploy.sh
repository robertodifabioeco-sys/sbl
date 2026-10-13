#!/usr/bin/env bash
# Pubblica il sito DEFINITIVO su friedmansociety.com (ramo gh-pages del repo sbl).
# Da usare solo dopo che i DNS del dominio puntano a GitHub Pages.
set -euo pipefail
cd "$(dirname "$0")/.."
python tools/build.py
python tools/check_links.py
NAME=$(git config user.name); MAIL=$(git config user.email)
TMP=$(mktemp -d)
cp -r dist/. "$TMP"/
cd "$TMP"
git init -q -b gh-pages
git config user.name "$NAME"
git config user.email "$MAIL"
git add -A
git commit -q -m "Sito SBL $(date +%Y-%m-%d\ %H:%M)"
git -c http.postBuffer=524288000 push -q -f https://github.com/robertodifabioeco-sys/sbl.git gh-pages
cd - >/dev/null
rm -rf "$TMP"
echo "Pubblicato: https://friedmansociety.com/"
