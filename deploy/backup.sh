#!/usr/bin/env bash
# Nightly backup of the SQLite DB + uploaded media. Keeps 14 days.
# Cron:  0 2 * * * /srv/rizendigital/deploy/backup.sh
set -euo pipefail
cd /srv/rizendigital
mkdir -p backups
STAMP=$(date +%F)
sqlite3 db.sqlite3 ".backup 'backups/db-$STAMP.sqlite3'"
tar -czf "backups/media-$STAMP.tar.gz" media
find backups -type f -mtime +14 -delete
