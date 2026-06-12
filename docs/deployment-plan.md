# Deployment Plan (v2)

Target: GCP Compute Engine e2-micro (always free, us-west1 Oregon — ~15ms from Vancouver)
Stack: Daphne running directly under systemd, SQLite, in-memory channel layer — no Docker, no Redis, no Postgres

> To switch to Redis + Postgres later, set `CHANNEL_LAYER_BACKEND=redis` and `DATABASE_URL=<postgres url>` in the server's `.env`.

---

## 1. Code changes (do these before leaving your machine)

- [x] Move `ALLOWED_HOSTS` to an env var in `settings.py`
- [x] Add `CSRF_TRUSTED_ORIGINS` from env var (required for HTTPS in Django 4+)
- [x] Add `whitenoise` to `requirements.txt`
- [x] Add `whitenoise.middleware.WhiteNoiseMiddleware` to `MIDDLEWARE` in `settings.py` (directly after `SecurityMiddleware`)
- [x] Add `STATIC_ROOT = BASE_DIR / "staticfiles"` to `settings.py`
- [x] Set `SESSION_COOKIE_SECURE = True` in `settings.py`
- [x] Set `CSRF_COOKIE_SECURE = True` in `settings.py`
- [x] Call `django.setup()` explicitly in `asgi.py` before app imports (required when Daphne is invoked directly)
- [x] Commit and push all of the above

## 2. Provision the server

- [x] Sign up / log in at https://console.cloud.google.com
- [x] Enable billing — a credit card is required but the e2-micro in us-west1 is always free and will not be charged
- [x] Create a new project (or use an existing one)
- [x] Go to Compute Engine → VM instances → Create instance:
  - Name: anything (e.g. `carrier-pigeon`)
  - Region: `us-west1` (Oregon) — required for always-free tier
  - Machine type: `e2-micro` (2 vCPU shared, 1GB RAM)
  - Boot disk: Ubuntu 22.04 LTS, 30GB standard persistent disk
  - Under "Advanced" → Security: paste your SSH public key
- [x] VPC network → Firewall: add rules allowing TCP 80 and TCP 443
- [x] Note the external IP address once the instance is running

## 3. Configure DNS

- [x] Create an A record in your DNS provider pointing your domain to the external IP
- [x] Wait for propagation — check with: `dig carrier-pigeon.duckdns.org`

## 4. Secure the server

- [x] SSH in (or use the GCP browser terminal)
- [x] Update packages: `sudo apt update && sudo apt upgrade -y`
- [x] Install and enable firewall:
  ```
  sudo apt install -y ufw
  sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
  ```

## 5. Install dependencies

- [x] Install Python 3.12 (Ubuntu 22.04 ships with 3.11; Django 6 requires 3.12+):
  ```
  sudo apt install -y software-properties-common curl gpg
  curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF23C5A6CF475977595C89F51BA6932366A755776" | sudo gpg --dearmor -o /usr/share/keyrings/deadsnakes.gpg
  echo "deb [signed-by=/usr/share/keyrings/deadsnakes.gpg] https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/deadsnakes.list
  sudo apt update && sudo apt install -y python3.12 python3.12-venv
  ```
- [x] Install git: `sudo apt install -y git`
- [x] Enable unattended security upgrades: `sudo apt install -y unattended-upgrades`

## 6. Install and configure Caddy (reverse proxy + TLS)

- [x] Install Caddy:
  ```
  sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
  sudo apt update && sudo apt install caddy
  ```
- [x] Create `/etc/caddy/Caddyfile`:
  ```
  carrier-pigeon.duckdns.org {
      reverse_proxy localhost:8000
  }
  ```
  Caddy automatically obtains a Let's Encrypt certificate, handles HTTPS, and correctly proxies WebSocket `Upgrade` headers.
- [x] Start Caddy: `sudo systemctl reload caddy`
- [x] Verify: `sudo systemctl status caddy`

## 7. Deploy the app

- [x] Run setup as root:
  ```
  sudo bash /path/to/scripts/setup.sh
  ```
  This clones the repo to `/opt/carrier-pigeon`, creates the `carrier-pigeon` system user, sets up the Python 3.12 virtualenv, installs dependencies, and registers the systemd units.

- [x] Create the `.env` file at `/opt/carrier-pigeon/.env`:
  ```
  DEBUG=false
  CHANNEL_LAYER_BACKEND=memory
  SECRET_KEY=<generate below>
  FERNET_KEY=<generate below>
  ALLOWED_HOSTS=carrier-pigeon.duckdns.org
  CSRF_TRUSTED_ORIGINS=https://carrier-pigeon.duckdns.org
  ```
- [x] Generate `SECRET_KEY`:
  ```
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- [x] Generate `FERNET_KEY`:
  ```
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [x] Run migrations and collect static files:
  ```
  sudo runuser -u carrier-pigeon -- /opt/carrier-pigeon/venv/bin/python /opt/carrier-pigeon/manage.py migrate
  sudo runuser -u carrier-pigeon -- /opt/carrier-pigeon/venv/bin/python /opt/carrier-pigeon/manage.py collectstatic --noinput
  ```
- [x] Start the service and enable auto-deploy timer:
  ```
  sudo systemctl start carrier-pigeon
  sudo systemctl enable carrier-pigeon
  sudo systemctl enable --now carrier-pigeon-deploy.timer
  ```
- [x] Check logs: `sudo journalctl -u carrier-pigeon -f`

## 8. Verify

- [x] Visit `https://carrier-pigeon.duckdns.org` — landing page loads with TLS padlock
- [x] Sign up for an account
- [x] Create a room and send a message
- [x] Open a second browser / incognito window, sign in as a different user, join the same room
- [x] Confirm messages appear in real time (verifies WebSockets are working through Caddy)
- [x] Confirm messages are encrypted at rest:
  ```
  sudo runuser -u carrier-pigeon -- /opt/carrier-pigeon/venv/bin/python /opt/carrier-pigeon/manage.py shell -c "from chat.models import Message; print(Message.objects.last().body)"
  ```
  Output should be a `gAAAAA...` Fernet blob, not plaintext.

## 9. Ongoing

- [x] Auto-deploy: a systemd timer polls GitHub every 10 minutes and runs `scripts/deploy.sh` if main has changed
- [x] To deploy manually: `sudo bash /opt/carrier-pigeon/scripts/deploy.sh`
- [x] To view logs: `sudo journalctl -u carrier-pigeon -f`
- [x] Enable unattended security upgrades: `sudo apt install unattended-upgrades`

## 10. Future work

> **Auto-deploy polish:** `scripts/setup.sh` should be updated to run the systemd install steps instead of printing them as instructions.

> **Dockerfile hardening:** pip runs as root inside the container (Docker is still used for local dev). For a proper production image, add a non-root user in the Dockerfile.

> **Zero-downtime deploys:** Ideally a deploy would spin up a new VM instance, wait for it to be healthy, then re-wire the load balancer and retire the old one (blue-green). Not straightforward here — there's no load balancer or instance group to swap behind.

---

## See also

- [Deploy postmortem](deploy-postmortem.md) — issues encountered during the initial deploy and how they were resolved
- [Reading list](reading-list.md) — docs for every tool used in this stack
