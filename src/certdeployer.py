#!/usr/bin/env python3
"""
CertDeployer - orchestrate certbot for multiple sites
Run as root. Requires certbot, PyYAML, and requests (for Slack notifications).
"""

import subprocess, sys, yaml, os, argparse, datetime, shlex, logging, time
from pathlib import Path
from datetime import timezone
import requests
import smtplib
from email.mime.text import MIMEText

DEFAULT_CONFIG = "/etc/certdeployer/sites.yml"
LOGFILE = "/var/log/certdeployer.log"

# Logging
logger = logging.getLogger("certdeployer")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOGFILE)
fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
fh.setFormatter(fmt)
logger.addHandler(fh)

# Helpers
def run(cmd, capture=False):
    logger.info("RUN: %s", cmd)
    if capture:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    subprocess.check_call(cmd, shell=True)

def cert_expiry_days(domain):
    crt = Path(f"/etc/letsencrypt/live/{domain}/cert.pem")
    if not crt.exists():
        return None
    out = subprocess.check_output(f"openssl x509 -enddate -noout -in {crt}", shell=True).decode().strip()
    if out.startswith("notAfter="):
        s = out[len("notAfter="):]
        expire = datetime.datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        now = datetime.datetime.now(timezone.utc)
        delta = expire - now
        return delta.days
    return None

def try_certbot_webroot(domains, webroot, email, staging):
    dom_args = " ".join([f"-d {d}" for d in domains])
    staging_arg = "--staging" if staging else ""
    cmd = f"certbot certonly --non-interactive --agree-tos --email {shlex.quote(email)} --webroot -w {shlex.quote(webroot)} {dom_args} {staging_arg} --quiet"
    try:
        run(cmd)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("certbot webroot failed for %s : %s", domains, e)
        return False

def try_certbot_nginx(domains, email, staging):
    dom_args = " ".join([f"-d {d}" for d in domains])
    staging_arg = "--staging" if staging else ""
    cmd = f"certbot --nginx --non-interactive --agree-tos --email {shlex.quote(email)} {dom_args} {staging_arg} --quiet"
    try:
        run(cmd)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("certbot nginx plugin failed for %s : %s", domains, e)
        return False

def reload_nginx():
    try:
        run("nginx -t")
    except subprocess.CalledProcessError:
        logger.error("nginx config test failed, not reloading")
        return False
    try:
        run("systemctl reload nginx")
        logger.info("nginx reloaded")
        return True
    except Exception as e:
        logger.error("failed to reload nginx: %s", e)
        return False

# Notification helpers
def notify_slack(webhook, message):
    try:
        requests.post(webhook, json={"text": message}, timeout=5)
    except Exception as e:
        logger.error("Slack notify failed: %s", e)

def notify_email(to_addr, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = f"certdeployer@{os.uname().nodename}"
        msg['To'] = to_addr
        with smtplib.SMTP('localhost') as s:
            s.send_message(msg)
    except Exception as e:
        logger.error("Email notify failed: %s", e)

# Main
def main(config_path, site_name=None):
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    staging = cfg.get("staging", True)
    email = cfg.get("default_email", "admin@example.com")
    threshold = cfg.get("renewal_threshold_days", 30)
    slack_webhook = cfg.get("notifications", {}).get("slack_webhook")
    email_addr = cfg.get("notifications", {}).get("email")
    sites = cfg.get("sites", [])
    if site_name:
        sites = [s for s in sites if s.get("name") == site_name]

    for s in sites:
        name = s.get("name")
        domains = s.get("domains", [])
        if not domains:
            logger.warning("site %s has no domains, skipping", name)
            continue
        primary = domains[0]
        days = cert_expiry_days(primary)
        logger.info("Site %s primary %s expiry days %s", name, primary, days)
        need = False
        if days is None:
            logger.info("No cert found for %s — issuing new cert", primary)
            need = True
        elif days <= threshold:
            logger.info("Cert for %s expiring in %s days (<= %s) — renewing", primary, days, threshold)
            need = True
        else:
            logger.info("Cert for %s not due for renewal (days=%s)", primary, days)

        if not need:
            continue

        success = False
        if s.get("webroot"):
            success = try_certbot_webroot(domains, s["webroot"], email, staging)
        if not success:
            logger.info("Trying certbot nginx plugin for %s", name)
            success = try_certbot_nginx(domains, email, staging)

        if not success:
            logger.error("All certbot attempts failed for %s", name)
            fail_msg = f"CertDeployer: FAILED to renew {name} ({', '.join(domains)})"
            if slack_webhook:
                notify_slack(slack_webhook, fail_msg)
            if email_addr:
                notify_email(email_addr, fail_msg, fail_msg)
            continue

        if reload_nginx():
            logger.info("Certificate deployed and nginx reloaded for %s", name)
        else:
            logger.error("Certificate deployed but nginx reload failed for %s", name)

        time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--site", default=None, help="optional, run only for single site name")
    args = parser.parse_args()
    main(args.config, args.site)
