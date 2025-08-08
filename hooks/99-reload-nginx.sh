#!/usr/bin/env bash
# Put this in /etc/letsencrypt/renewal-hooks/deploy/
set -e
nginx -t && systemctl reload nginx || echo "nginx reload failed" >&2