#!/bin/bash
set -e

APP_DIR=/opt/carrier-pigeon
APP_USER=carrier-pigeon

cd $APP_DIR

runuser -u $APP_USER -- git fetch origin main
CURRENT=$(runuser -u $APP_USER -- git rev-parse HEAD)
LATEST=$(runuser -u $APP_USER -- git rev-parse origin/main)

if [ "$CURRENT" = "$LATEST" ]; then
    exit 0
fi

runuser -u $APP_USER -- git pull
runuser -u $APP_USER -- $APP_DIR/venv/bin/pip install -r requirements.txt
runuser -u $APP_USER -- $APP_DIR/venv/bin/python manage.py migrate
runuser -u $APP_USER -- $APP_DIR/venv/bin/python manage.py collectstatic --noinput
systemctl restart carrier-pigeon
