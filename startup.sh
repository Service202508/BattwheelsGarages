#!/bin/bash
# Battwheels OS - Startup Script
# Ensures all system dependencies are installed before backend starts.
# This script handles dependencies that cannot be committed to the container image
# and must be installed on each new fork/deployment.

set -e

echo "[startup.sh] Installing WeasyPrint PDF generation dependencies..."
apt-get install -y --quiet \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    2>&1 | tail -3

echo "[startup.sh] WeasyPrint dependencies installed. PDF generation ready."
