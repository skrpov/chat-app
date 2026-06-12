# Reading List

Tools and technologies used in this project, with pointers to the most useful docs.

---

## Application

**Django**  
Python web framework. Core concepts: models, views, URLs, middleware, settings.  
https://docs.djangoproject.com/en/stable/

**Django Channels**  
Extends Django to handle WebSockets and other async protocols via ASGI.  
https://channels.readthedocs.io/en/stable/

**Daphne**  
The ASGI server that serves Django Channels applications in production.  
https://github.com/django/daphne

**whitenoise**  
Serves static files directly from the Django/Daphne process without a separate file server.  
https://whitenoise.readthedocs.io/en/stable/

---

## Infrastructure

**Caddy**  
Reverse proxy and web server. Handles TLS certificate provisioning and renewal automatically via Let's Encrypt. The Caddyfile format and automatic HTTPS docs are the most useful sections.  
https://caddyserver.com/docs/

**systemd**  
Linux service and process manager. Used here to keep Daphne running and auto-deploy on a timer. Key concepts: unit files, `systemctl`, `journalctl`, timers.  
https://systemd.io/  
https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html  
https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html

**UFW (Uncomplicated Firewall)**  
Frontend for `iptables` on Ubuntu. Used to restrict inbound traffic to SSH, HTTP, and HTTPS only.  
https://help.ubuntu.com/community/UFW

**Docker / Docker Compose**  
Container runtime and multi-service orchestration. Still in the repo for local development.  
https://docs.docker.com/  
https://docs.docker.com/compose/

---

## Hosting / DNS

**GCP Compute Engine**  
Google's VM hosting. The `e2-micro` in `us-west1` is part of the always-free tier.  
https://cloud.google.com/compute/docs

**DuckDNS**  
Free dynamic DNS service. Provides a `*.duckdns.org` subdomain pointing to your server IP.  
https://www.duckdns.org/

**Let's Encrypt**  
Free TLS certificate authority used by Caddy under the hood.  
https://letsencrypt.org/how-it-works/

---

## Python / Environment

**deadsnakes PPA**  
Provides newer Python versions for Ubuntu. Used to install Python 3.12 on Ubuntu 22.04.  
https://github.com/deadsnakes/

**Python venv**  
Built-in virtual environment tool. Used to isolate the app's dependencies from the system Python.  
https://docs.python.org/3/library/venv.html

**Fernet (cryptography library)**  
Symmetric encryption used to encrypt messages at rest.  
https://cryptography.io/en/latest/fernet/
