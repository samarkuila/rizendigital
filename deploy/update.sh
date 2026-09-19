#!/usr/bin/env bash
# Deploy new code: run on the server after uploading/pulling the changes.
set -euo pipefail
cd /srv/rizendigital
./venv/bin/pip install -r requirements.txt
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py collectstatic --noinput
sudo chgrp -R www-data staticfiles && sudo chmod -R g+rX staticfiles
sudo systemctl restart rizendigital
