FROM debian:bookworm-slim

# Bookworm ships Python 3.11, so 3.12 comes from the deadsnakes PPA, the same
# way it is installed on the VM (see docs/deployment-plan.md).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg \
    && curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF23C5A6CF475977595C89F51BA6932366A755776" \
        | gpg --dearmor -o /usr/share/keyrings/deadsnakes.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/deadsnakes.gpg] https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" \
        > /etc/apt/sources.list.d/deadsnakes.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.12 python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Outside /app because compose bind-mounts the source tree over it.
RUN python3.12 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["./entrypoint.sh"]
