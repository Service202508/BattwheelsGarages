#!/bin/bash
# Battwheels OS - Production Startup Script
# This script is the container entrypoint for production deployments.
# It checks dependencies and then starts supervisord to manage all services.

echo "[startup.sh] Starting Battwheels OS..."

# Ensure log directory exists
mkdir -p /var/log/supervisor

# Check WeasyPrint PDF generation dependencies (non-fatal)
echo "[startup.sh] Checking WeasyPrint PDF generation dependencies..."
dpkg -l libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libharfbuzz0b >/dev/null 2>&1 && \
    echo "[startup.sh] WeasyPrint dependencies already installed." || \
    echo "[startup.sh] Some WeasyPrint dependencies may be missing (non-fatal)."

# Start supervisord as the main process (foreground mode via nodaemon=true)
echo "[startup.sh] Starting supervisord..."
exec /usr/bin/supervisord -c /app/supervisord.prod.conf
