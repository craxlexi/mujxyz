#!/usr/bin/env bash
set -euo pipefail
cd /opt/mujheky
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=l

id -u mujheky >/dev/null 2>&1 || useradd --system --home /opt/mujheky --shell /usr/sbin/nologin mujheky
install -d -o mujheky -g mujheky -m 0755 backend/data python .cache .venv .local/bin
test -x bootstrap/bin/uv || { python3 -m venv bootstrap; bootstrap/bin/pip -q install uv; }
runuser -u mujheky -- env UV_PYTHON_INSTALL_DIR=/opt/mujheky/python UV_CACHE_DIR=/opt/mujheky/.cache/uv bootstrap/bin/uv --no-config python install 3.12
if [ ! -x .venv/bin/python ]; then
    runuser -u mujheky -- env UV_PYTHON_INSTALL_DIR=/opt/mujheky/python UV_CACHE_DIR=/opt/mujheky/.cache/uv bootstrap/bin/uv --no-config venv --python 3.12 .venv
fi
runuser -u mujheky -- env UV_CACHE_DIR=/opt/mujheky/.cache/uv bootstrap/bin/uv --no-config pip install --python .venv/bin/python -r backend/requirements.txt
.venv/bin/python deploy/production/create_environment.py
chown mujheky:mujheky backend/.env
chmod 0600 backend/.env

if ! command -v caddy >/dev/null 2>&1; then
    curl -1fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key -o /tmp/mujheky-caddy-key.asc
    gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg /tmp/mujheky-caddy-key.asc
    curl -1fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
    chmod 0644 /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -o Dir::Etc::sourcelist=sources.list.d/caddy-stable.list -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0
    apt-get install -y caddy
fi

install -m 0644 deploy/production/mujheky-api.service /etc/systemd/system/mujheky-api.service
install -m 0644 deploy/production/mujheky-worker.service /etc/systemd/system/mujheky-worker.service
install -m 0644 deploy/production/Caddyfile /etc/caddy/Caddyfile
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl daemon-reload
systemctl enable --now mujheky-api mujheky-worker caddy
systemctl reload caddy
systemctl is-active mujheky-api mujheky-worker caddy
