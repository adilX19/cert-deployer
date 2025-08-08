# CertDeployer

SSL Auto-Provisioning Utility — orchestrates Certbot to issue and renew TLS certs for many subdomains and deploy to NGINX.

## Features

- Config-driven (YAML) list of sites
- Uses webroot first, falls back to certbot nginx plugin
- Checks certificate expiry and renews only when needed
- Logs to `/var/log/certdeployer.log`
- Includes systemd timer and optional cron

## Quick install (example)

```bash
# copy repo to /opt/certdeployer
sudo cp -r certdeployer /opt/
sudo /opt/certdeployer/bin/install.sh

```

## Notes

- Test with staging: staging: true in sites.yml
- For wildcards use DNS plugins (cloudflare, route53, etc.)

See conf/sites.yml.example and src/certdeployer.py for configuration.

## Usage notes

- Edit /etc/certdeployer/sites.yml (copy from conf/sites.yml.example).
- Initially keep staging: true while testing to use Let's Encrypt staging.
- After testing set staging: false and run sudo systemctl start certdeployer.service to obtain production certs.
- For wildcard certs use DNS provider plugins and add DNS provider entries in the sites.yml.
- Ensure the server can send mail locally (postfix or similar installed) for email notifications.
- For Slack, create an Incoming Webhook in your workspace and place its URL in sites.yml.
- Notifications trigger only when certificate acquisition/renewal fails.
