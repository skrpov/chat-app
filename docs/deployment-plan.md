# Deployment Plan (v1)

Target: GCP Compute Engine e2-micro (always free, us-west1 Oregon — ~15ms from Vancouver)
Stack: single Django/Daphne container, SQLite, in-memory channel layer — no Redis, no Postgres

> To switch to Redis + Postgres later, set `CHANNEL_LAYER_BACKEND=redis` and `DATABASE_URL=<postgres url>` in the server's `.env`.

---

## 1. Code changes (do these before leaving your machine)

- [ ] Move `ALLOWED_HOSTS` to an env var in `settings.py`
- [ ] Add `CSRF_TRUSTED_ORIGINS` from env var (required for HTTPS in Django 4+)
- [ ] Add `whitenoise` to `requirements.txt`
- [ ] Add `whitenoise.middleware.WhiteNoiseMiddleware` to `MIDDLEWARE` in `settings.py` (directly after `SecurityMiddleware`)
- [ ] Add `STATIC_ROOT = BASE_DIR / "staticfiles"` to `settings.py`
- [ ] Add `python manage.py collectstatic --noinput` to `entrypoint.sh` so static files are collected on every container start
- [ ] Set `SESSION_COOKIE_SECURE = True` in `settings.py`
- [ ] Set `CSRF_COOKIE_SECURE = True` in `settings.py`
- [ ] Commit and push all of the above

## 2. Provision the server

- [ ] Sign up / log in at https://console.cloud.google.com
- [ ] Enable billing — a credit card is required but the e2-micro in us-west1 is always free and will not be charged
- [ ] Create a new project (or use an existing one)
- [ ] Go to Compute Engine → VM instances → Create instance:
  - Name: anything (e.g. `chat-app`)
  - Region: `us-west1` (Oregon) — required for always-free tier
  - Machine type: `e2-micro` (2 vCPU shared, 1GB RAM)
  - Boot disk: Ubuntu 22.04 LTS, 30GB standard persistent disk
  - Under "Advanced" → Security: paste your SSH public key
- [ ] Under VPC network → Firewall: allow HTTP and HTTPS traffic (checkboxes on the instance creation page)
- [ ] Note the external IP address once the instance is running

## 3. Configure DNS

- [ ] Create an A record in your DNS provider pointing your domain to the external IP
- [ ] Wait for propagation — check with: `dig yourdomain.com`

## 4. Secure the server

- [ ] SSH in: `ssh <your-username>@<ip>`
- [ ] Update packages: `sudo apt update && sudo apt upgrade -y`
- [ ] Enable firewall: `sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable`

## 5. Install dependencies

- [ ] Install Docker: `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER`
  - Log out and back in after this so the group change takes effect
- [ ] Verify: `docker --version && docker compose version`
- [ ] Install git: `sudo apt install -y git`

## 6. Install and configure Caddy (reverse proxy + TLS)

- [ ] Install Caddy:
  ```
  sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
  sudo apt update && sudo apt install caddy
  ```
- [ ] Create `/etc/caddy/Caddyfile` (replace `yourdomain.com`):
  ```
  yourdomain.com {
      reverse_proxy localhost:8000
  }
  ```
  Caddy automatically obtains a Let's Encrypt certificate, handles HTTPS, and correctly proxies WebSocket `Upgrade` headers.
- [ ] Start Caddy: `sudo systemctl reload caddy`
- [ ] Verify: `sudo systemctl status caddy`

## 7. Deploy the app

- [ ] Clone the repo: `git clone https://github.com/skrpov/chat-app.git && cd chat-app`
- [ ] Create the `.env` file: `nano .env`
- [ ] Populate `.env`:
  ```
  DEBUG=false
  CHANNEL_LAYER_BACKEND=memory
  SECRET_KEY=<generate below>
  FERNET_KEY=<generate below>
  ALLOWED_HOSTS=yourdomain.com
  CSRF_TRUSTED_ORIGINS=https://yourdomain.com
  ```
- [ ] Generate `SECRET_KEY`:
  ```
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- [ ] Generate `FERNET_KEY`:
  ```
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] Start only the Django container (no Redis needed):
  ```
  docker compose up django-web -d --build
  ```
- [ ] Run migrations: `docker compose exec django-web python manage.py migrate`
- [ ] Check logs: `docker compose logs django-web`

## 8. Verify

- [ ] Visit `https://yourdomain.com` — landing page loads with TLS padlock
- [ ] Sign up for an account
- [ ] Create a room and send a message
- [ ] Open a second browser / incognito window, sign in as a different user, join the same room
- [ ] Confirm messages appear in real time (verifies WebSockets are working through Caddy)
- [ ] Confirm messages are encrypted at rest:
  ```
  docker compose exec django-web python manage.py shell -c "from chat.models import Message; print(Message.objects.last().body)"
  ```
  Output should be a `gAAAAA...` Fernet blob, not plaintext.

## 9. Ongoing

- [ ] Set up Docker log rotation to prevent disk fill — add to `/etc/docker/daemon.json`:
  ```json
  { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
  ```
  Then restart Docker: `sudo systemctl restart docker`
- [ ] Enable unattended security upgrades: `sudo apt install unattended-upgrades`
- [ ] To deploy a new version: `git pull && docker compose up django-web -d --build`
