#!/usr/bin/env bash
# One-time server setup for Ubuntu 24.04 (run as the `ubuntu` user).
# Usage:  bash /srv/rizendigital/deploy/setup.sh
set -euo pipefail
APP=/srv/rizendigital

# Small instances (1 GB RAM) need swap so pip/collectstatic cannot run out of memory
if ! swapon --show | grep -q .; then
    sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx sqlite3 ufw

cd "$APP"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

[ -f .env ] || { echo "Create $APP/.env first (copy .env.example and fill it in)"; exit 1; }
chmod 600 .env

mkdir -p media backups
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py collectstatic --noinput
./venv/bin/python manage.py check --deploy || true

# nginx must be able to read static/media
sudo chgrp -R www-data "$APP/staticfiles" "$APP/media"
sudo chmod -R g+rX "$APP/staticfiles" "$APP/media"
sudo chmod 711 /srv "$APP"

sudo cp deploy/gunicorn.service /etc/systemd/system/rizendigital.service
sudo cp deploy/nginx.conf /etc/nginx/sites-available/rizendigital
sudo ln -sf /etc/nginx/sites-available/rizendigital /etc/nginx/sites-enabled/rizendigital
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl enable --now rizendigital
sudo nginx -t && sudo systemctl reload nginx

sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw --force enable
echo "Done. Point DNS at this server, then run:  sudo certbot --nginx -d rizendigital.com -d www.rizendigital.com"
