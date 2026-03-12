#!/bin/bash
echo "[startup.sh] Starting Battwheels OS..."
mkdir -p /var/log/supervisor

echo "[startup.sh] Applying nginx proxy config..."
cp /app/nginx-proxy.conf /etc/nginx/sites-enabled/default
nginx -t && nginx -s reload || service nginx restart
echo "[startup.sh] Nginx configured."

echo "[startup.sh] Checking WeasyPrint dependencies..."
dpkg -l libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libharfbuzz0b >/dev/null 2>&1 && \
    echo "[startup.sh] WeasyPrint dependencies OK." || \
    echo "[startup.sh] Some WeasyPrint dependencies may be missing (non-fatal)."

echo "[startup.sh] Starting supervisord..."
exec /usr/bin/supervisord -c /app/supervisord.prod.conf
