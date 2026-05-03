#!/bin/sh
set -e

REPO="mb-mensa/mb-mensa.github.io"
WORK_DIR="/tmp/mb-mensa-repo"
KEY_FILE=$(mktemp)

cleanup() {
    rm -f "$KEY_FILE"
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

echo "$DEPLOY_KEY" | base64 -d > "$KEY_FILE"
chmod 600 "$KEY_FILE"

export GIT_SSH_COMMAND="ssh -i $KEY_FILE -o StrictHostKeyChecking=accept-new"

git clone "git@github.com:${REPO}" "$WORK_DIR"
cd "$WORK_DIR"

git config user.email "mb-mensa-updater@users.noreply.github.com"
git config user.name "mb-mensa-updater"

python mb-mensa-updater/fetch_menu_pdf.py
python mb-mensa-updater/parse_menu_pdf.py

NEWEST=$(ls -t html_menus/*.html | head -1)
cp "$NEWEST" index.html

git add index.html pdf_menus/ html_menus/
git commit -m "Update menu $(date +%Y_KW%V)" || echo "Nothing to commit"
git push

