#!/bin/bash
set -e

APP_DIR=/opt/carrier-pigeon
APP_USER=carrier-pigeon

useradd --system --no-create-home --shell /usr/sbin/nologin $APP_USER

git clone https://github.com/skrpov/chat-app.git $APP_DIR
chown -R $APP_USER:$APP_USER $APP_DIR

mkdir -p $APP_DIR/data
chown $APP_USER:$APP_USER $APP_DIR/data

runuser -u $APP_USER -- python3 -m venv $APP_DIR/venv
runuser -u $APP_USER -- $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

echo "Create $APP_DIR/.env before starting the service."
echo "Then run: cp $APP_DIR/scripts/carrier-pigeon.service /etc/systemd/system/"
echo "          cp $APP_DIR/scripts/carrier-pigeon-deploy.service /etc/systemd/system/"
echo "          cp $APP_DIR/scripts/carrier-pigeon-deploy.timer /etc/systemd/system/"
echo "          systemctl daemon-reload"
echo "          systemctl enable --now carrier-pigeon"
echo "          systemctl enable --now carrier-pigeon-deploy.timer"
