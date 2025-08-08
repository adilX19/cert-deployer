#!/usr/bin/env bash
set -euo pipefail

PREFIX=/opt/certdeployer
sudo mkdir -p ${PREFIX}
sudo cp -r . ${PREFIX}/
# Install python deps
if command -v pip3 >/dev/null 2>&1; then
  sudo pip3 install -r ${PREFIX}/requirements.txt
else
  echo "pip3 not found — install python3-pip and rerun"
  exit 1
fi
# copy example config
sudo mkdir -p /etc/certdeployer
sudo cp ${PREFIX}/conf/sites.yml.example /etc/certdeployer/sites.yml
sudo cp ${PREFIX}/conf/ssl_params.conf.example /etc/nginx/snippets/ssl_params.conf
# systemd
sudo cp ${PREFIX}/systemd/certdeployer.service /etc/systemd/system/
sudo cp ${PREFIX}/systemd/certdeployer.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now certdeployer.timer

# create log
sudo touch /var/log/certdeployer.log
sudo chown root:root /var/log/certdeployer.log
sudo chmod 640 /var/log/certdeployer.log

echo "Installed to ${PREFIX}. Edit /etc/certdeployer/sites.yml and run systemctl start certdeployer.service to test."