# Deploy Postmortem

Issues encountered during the initial deployment of Carrier Pigeon to GCP.

---

## 1. Stale Docker image after adding whitenoise
**Symptom:** `ModuleNotFoundError: No module named 'whitenoise'` in container logs.  
**Cause:** `whitenoise` was added to `requirements.txt` but the image wasn't rebuilt.  
**Fix:** `docker compose up --build` to force a rebuild.

## 2. "Messenger" branding left in auth templates
**Symptom:** Login, signup, logout, and sidebar still showed "Messenger" after the rename.  
**Cause:** The initial rename only covered `landing.html` and `base.html`; auth templates under `accounts/templates/` were missed.  
**Fix:** Grepped all templates for "Messenger" and replaced in the four remaining files.

## 3. WebSocket used `ws://` on an HTTPS page
**Symptom:** Joe's browser blocked the WebSocket connection with a Mixed Content error; messages never arrived in real time.  
**Cause:** The WebSocket URL was hardcoded to `ws://` regardless of page protocol.  
**Fix:** `(window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + ...`

## 4. `REDIS_PASSWORD` variable warning from Docker Compose
**Symptom:** `WARN: The "REDIS_PASSWORD" variable is not set. Defaulting to a blank string.`  
**Cause:** The `redis` service used `${REDIS_PASSWORD}` with no default, so Compose warned even when the service wasn't started.  
**Fix:** Changed to `${REDIS_PASSWORD:-}` to make the empty default explicit.

## 5. Container didn't recover after Docker daemon restart
**Symptom:** After restarting the Docker daemon for log rotation, the container was running but port 8000 was unbound — Caddy got connection refused.  
**Cause:** No `restart: always` on the `django-web` service, so Docker didn't re-establish port bindings after the daemon restart.  
**Fix:** Added `restart: always` to the service. (This became moot after switching to systemd, but the root cause was the missing restart policy.)

## 6. Intermittent 502 on page refresh (Caddy ↔ Django)
**Symptom:** Every other page refresh returned a 502; `sudo systemctl reload caddy` fixed it.  
**Cause:** Caddy's connection to the backend was in a bad state after container restarts.  
**Fix:** Reload Caddy after any container restart to re-establish upstream connections.

## 7. SSH from local machine failed
**Symptom:** `Permission denied (publickey)` when SSHing into the VM.  
**Cause:** GCP derives the Linux username from the SSH key's comment field or project metadata; the correct username (`skarpov03`) wasn't obvious.  
**Fix:** Used GCP's browser-based SSH terminal throughout. Determined correct username via `whoami`.

## 8. `ufw` not installed
**Symptom:** `ufw: command not found`.  
**Cause:** The Ubuntu 22.04 image on GCP doesn't ship with UFW by default.  
**Fix:** `sudo apt install -y ufw` before running firewall commands.

## 9. `add-apt-repository` crashed adding deadsnakes PPA
**Symptom:** Python traceback: `AttributeError: 'NoneType' object has no attribute 'people'`.  
**Cause:** Known bug in `software-properties-common` on some Ubuntu 22.04 versions when contacting Launchpad.  
**Fix:** Added the PPA manually via `curl` + `gpg` + writing to `/etc/apt/sources.list.d/`.

## 10. VM shipped with Python 3.11; Django 6.0.5 requires Python 3.12+
**Symptom:** `ERROR: No matching distribution found for Django==6.0.5`.  
**Cause:** Ubuntu 22.04's default Python is 3.11; Django 6 dropped support for anything below 3.12.  
**Fix:** Installed Python 3.12 from the deadsnakes PPA and recreated the virtualenv with `python3.12`.

## 11. Virtualenv created without pip
**Symptom:** `venv/bin/` contained only `python`, `python3`, `python3.11` — no `pip`.  
**Cause:** System Python 3.11 didn't have the `ensurepip` module available (common on minimal Ubuntu installs).  
**Fix:** Installed `python3.12-venv` which includes pip, then recreated the venv with `python3.12 -m venv --clear`.

## 12. `AppRegistryNotReady` when running Daphne directly
**Symptom:** `django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.` on startup.  
**Cause:** When running `manage.py runserver`, Django's management command infrastructure calls `django.setup()` automatically. Running `daphne config.asgi:application` directly just imports the module — `setup()` is never called, so models imported at module level in `asgi.py` fail.  
**Fix:** Added `import django; django.setup()` in `asgi.py` after `os.environ.setdefault(...)`.

## 13. Typo in systemd unit: `Enviroment` instead of `Environment`
**Symptom:** `DJANGO_SETTINGS_MODULE` wasn't set despite being in the unit file; same `AppRegistryNotReady` error persisted.  
**Cause:** Typo when editing the file manually in `nano`.  
**Fix:** Corrected spelling, reloaded daemon, restarted service.

## 14. Static files not collected on initial direct install
**Symptom:** JS files returned `text/html` (Django's 404 page) with `NS_ERROR_CORRUPTED_CONTENT`.  
**Cause:** `collectstatic` had only been run inside the Docker container. The new direct install had no `staticfiles/` directory.  
**Fix:** Ran `manage.py collectstatic --noinput` manually; `deploy.sh` already includes this for future deploys.
