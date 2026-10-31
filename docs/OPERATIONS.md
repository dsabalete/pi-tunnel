# Operations Runbook

## System Monitoring

The `/status` command reports host metrics via Telegram.

Public IP caching: The public IP address fetched from `https://api.ipify.org` is cached in-memory for 10 minutes (600s TTL) to avoid rate-limiting external service. Cache is per-process and resets on bot restart. After TTL expiry, next `/status` call triggers a fresh HTTP request with 3s timeout. On timeout or error, public IP is reported as `unknown`.
