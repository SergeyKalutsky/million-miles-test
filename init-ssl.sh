#!/bin/bash

DOMAIN="million-miles-test.polyglotty.online"
EMAIL="skalutsky@gmail.com"

set -e

echo "=== Creating certbot directories ==="
mkdir -p ./certbot/conf ./certbot/www

echo "=== Starting temporary nginx on port 80 for ACME challenge ==="

# Create a self-signed dummy cert so nginx can start with the 443 block present
if [ ! -f ./certbot/conf/live/$DOMAIN/fullchain.pem ]; then
    mkdir -p ./certbot/conf/live/$DOMAIN
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout ./certbot/conf/live/$DOMAIN/privkey.pem \
        -out    ./certbot/conf/live/$DOMAIN/fullchain.pem \
        -subj   "/CN=localhost" 2>/dev/null
    echo "Dummy self-signed cert created."
fi

echo "=== Starting frontend container ==="
docker compose up -d frontend

echo "=== Requesting real Let's Encrypt certificate ==="
# Run certbot directly (not via docker compose run) to avoid container startup issues
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

echo "=== Restarting frontend so nginx picks up the real certificate ==="
# Restart (not just reload) so the volume is re-mounted with the real cert
docker compose restart frontend

echo "=== Bringing up the full stack ==="
docker compose up -d

echo "=== Done! Certificate issued for $DOMAIN ==="
echo "    Site: https://$DOMAIN"
