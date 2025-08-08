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

## Wildcard certs & DNS challenge

- If you need \*.example.com, you must use DNS challenge (--manual is one way but not automated). Better: install certbot DNS plugin for your provider (e.g., certbot-dns-cloudflare) and call:

```bash
certbot certonly --dns-cloudflare --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.env -d example.com -d '*.example.com'
```

-Store provider API keys in a safe env file (/etc/letsencrypt/cloudflare.env) with permissions 600.

## Testing / dry-run

1. Set staging: true in config to hit Let's Encrypt staging (no rate-limit worry).
2. Run: sudo /usr/local/bin/certdeployer.py --config /etc/certdeployer/sites.yml
3. Check /var/log/certdeployer.log. Check certbot certificates to see issued cert.
4. Test nginx config nginx -t
5. Try hitting the site with curl -v https://app1.example.com (will fail if staging cert untrusted — that's expected during staging)
6. When done testing, set staging: false.

## Safety & gotchas

- Rate limits: use staging while testing; stagger requests; for many new domains avoid requesting more than Let’s Encrypt’s create rate limit (watch docs).
- Multiple domains per cert: combining many domains into a single certificate counts against rate limits differently — consider separate certs per app.
- nginx plugin can change config; webroot is less invasive but needs correct webroot mapping.
- Make sure SELinux/AppArmor policies allow certbot to write to webroot.
- Keep /etc/letsencrypt backed up if you migrate servers.

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

## Testing checklist (short)

- Confirm DNS A/AAAA records point to server.
- NGINX serves /.well-known/acme-challenge from webroot.
- Run with staging: true and verify certificate file created under /etc/letsencrypt/live/<domain>/.
- nginx -t passes and reload works.
- Run certdeployer.py as systemd timer and verify log output.
- Disable staging and re-run carefully.

### If you must use cron, add cron job:

```swift
0 3 * * * /usr/local/bin/certdeployer.py --config /etc/certdeployer/sites.yml >> /var/log/certdeployer.log 2>&1
```
