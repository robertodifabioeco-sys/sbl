#!/usr/bin/env bash
# Pubblica l'anteprima su https://robertodifabioeco-sys.github.io/sbl/ (ramo gh-pages del repo sbl).
set -euo pipefail
cd "$(dirname "$0")/.."
python tools/build.py --preview
python tools/check_links.py >/dev/null || true
NAME=$(git config user.name); MAIL=$(git config user.email)
TMP=$(mktemp -d)
cp -r dist-preview/. "$TMP"/
cd "$TMP"
git init -q -b gh-pages
git config user.name "$NAME"
git config user.email "$MAIL"
git add -A
git commit -q -m "Anteprima sito SBL $(date +%Y-%m-%d\ %H:%M)"
git -c http.postBuffer=524288000 push -q -f https://github.com/robertodifabioeco-sys/sbl.git gh-pages
cd - >/dev/null
rm -rf "$TMP"
echo "Pubblicato: https://robertodifabioeco-sys.github.io/sbl/"
