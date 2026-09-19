# Deploying Rizen Digital to AWS (EC2 or Lightsail)

The server steps (2 onwards) are identical on EC2 and Lightsail. Step 1 below is for Lightsail; for EC2 create an Ubuntu 24.04 instance (t3.micro or t3.small, 20 GB gp3), attach an Elastic IP, and open ports 22/80/443 in its security group.

Stack: Ubuntu 24.04 → nginx (TLS, static, media) → gunicorn → Django, SQLite database.
Everything runs on one small server. Estimated cost: ~$7/month (1 GB plan) plus a free static IP.

## 1. Create the server (AWS console)
1. Lightsail → **Create instance** → Linux/Unix → **OS only → Ubuntu 24.04 LTS**.
2. Plan: **1 GB RAM** (the 512 MB plan is too tight for pip installs). Region: **Mumbai (ap-south-1)** for Indian visitors.
3. Name it `rizendigital`, create it.
4. **Networking → Create static IP** and attach it to the instance (so the IP survives reboots).
5. **Networking → IPv4 Firewall**: allow SSH (22), HTTP (80), HTTPS (443). Restrict SSH to your own IP if possible.
6. Turn on **automatic snapshots** (Snapshots tab) as a second backup layer.

## 2. Upload the project
From your PC (PowerShell, in `D:\RD`), replace `SERVER_IP` and the key path (download the default key from Lightsail → Account → SSH keys):

```powershell
# code (excludes secrets, caches, local venv)
tar --exclude=venv --exclude=__pycache__ --exclude=.env --exclude=staticfiles --exclude=media --exclude=db.sqlite3 -czf rizen.tgz -C rizendigital .
scp -i C:\path\LightsailDefaultKey.pem rizen.tgz ubuntu@SERVER_IP:/tmp/
# database + uploaded images (your real content)
scp -i C:\path\LightsailDefaultKey.pem rizendigital\db.sqlite3 ubuntu@SERVER_IP:/tmp/
scp -i C:\path\LightsailDefaultKey.pem -r rizendigital\media ubuntu@SERVER_IP:/tmp/media   # skip if the folder does not exist
```

On the server (`ssh -i key ubuntu@SERVER_IP`):

```bash
sudo mkdir -p /srv/rizendigital && sudo chown ubuntu:ubuntu /srv/rizendigital
tar -xzf /tmp/rizen.tgz -C /srv/rizendigital
mv /tmp/db.sqlite3 /srv/rizendigital/
[ -d /tmp/media ] && mv /tmp/media /srv/rizendigital/media
cp /srv/rizendigital/.env.example /srv/rizendigital/.env
nano /srv/rizendigital/.env      # see step 3
```

## 3. Fill in `.env` on the server
Generate a secret key: `python3 -c "import secrets;print(secrets.token_urlsafe(50))"`

```
DJANGO_SECRET_KEY=<generated value>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=rizendigital.com,www.rizendigital.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://rizendigital.com,https://www.rizendigital.com
DJANGO_SSL_REDIRECT=False       # temporarily, until step 6 is done
EMAIL_HOST_USER=...             # Gmail address + app password for lead emails
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=...
```

Never copy your local `.env` or commit secrets. The app refuses to start with `DEBUG=False` and the default insecure key.

## 4. Install and start
```bash
bash /srv/rizendigital/deploy/setup.sh
```
Visit `http://SERVER_IP/` (you may see a host error until DNS is set; add the IP to `DJANGO_ALLOWED_HOSTS` temporarily to test, then remove it).

## 5. Point the domain (at your registrar)
Create DNS records:

| Type | Name | Value |
|------|------|-------|
| A | @ | your static IP |
| A | www | your static IP |

Wait for propagation (minutes to a few hours). Check with `nslookup rizendigital.com`.

## 6. HTTPS
```bash
sudo certbot --nginx -d rizendigital.com -d www.rizendigital.com
```
Then set `DJANGO_SSL_REDIRECT=True` in `.env` and `sudo systemctl restart rizendigital`.
Certificates renew automatically (check: `sudo certbot renew --dry-run`).
After a week of stable HTTPS you may raise `DJANGO_HSTS_SECONDS` to `31536000`.

## 7. Backups
```bash
crontab -e     # add:
0 2 * * * /srv/rizendigital/deploy/backup.sh
```
Backups (DB + media, 14 days) land in `/srv/rizendigital/backups`. Periodically copy them off the server (S3 or your PC) and keep the Lightsail snapshots on.

## 8. Everyday operations
- **Deploy changes:** upload new code (repeat the tar/scp step, extracting over `/srv/rizendigital`), then `bash /srv/rizendigital/deploy/update.sh`.
- **Logs:** `sudo journalctl -u rizendigital -f` and `/var/log/nginx/error.log`.
- **Restart:** `sudo systemctl restart rizendigital`.
- **Admin:** `https://rizendigital.com/admin/` (create a strong password; `python manage.py changepassword <user>`).

## 9. After go-live
- When you have a real phone number and social profiles, add `SITE_PHONE` (e.g. `+919812345678`) and `SITE_FACEBOOK_URL` / `SITE_INSTAGRAM_URL` / etc. to `.env` and restart. They then appear in the header, footer, contact page and structured data automatically; until then they stay hidden.
- Add your real street address to the footer and structured data.
- Submit `https://rizendigital.com/sitemap.xml` in Google Search Console and verify the domain.
- Create the Google Business Profile.

## Limits of this setup
Single server = a short outage during reboots and no automatic failover; SQLite is fine for this traffic but is not suited to multiple servers. If traffic grows, move to RDS PostgreSQL and S3 for media.
