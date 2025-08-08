#!/usr/bin/env bash
# wrapper for cron or manual runs
PY=/usr/bin/python3
CFG=/etc/certdeployer/sites.yml
$PY /opt/certdeployer/src/certdeployer.py --config "$CFG" "$@"