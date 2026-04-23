#!/bin/bash
set -e

# Start ZAP daemon in the background
echo "Starting ZAP Daemon..."
/opt/zap/zap.sh -daemon -host 127.0.0.1 -port 8080 -config api.disablekey=true > /var/log/zap.log 2>&1 &

# Wait for ZAP to boot
echo "Waiting for ZAP to initialize on port 8080..."
while ! curl -s http://127.0.0.1:8080/JSON/core/view/version > /dev/null; do
    sleep 1
done
echo "ZAP initialized."

# Execute the passed command (e.g., sentinel)
exec "$@"
