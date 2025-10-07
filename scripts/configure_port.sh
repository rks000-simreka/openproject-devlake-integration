#!/bin/bash

# Script to configure Grafana port and check for conflicts
# This script helps avoid port conflicts and ensures Grafana runs on available port

echo "🔧 Grafana Port Configuration Script"
echo "===================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep ":$port " >/dev/null 2>&1
    elif command -v ss >/dev/null 2>&1; then
        ss -tuln | grep ":$port " >/dev/null 2>&1
    else
        # Fallback using lsof
        lsof -i :$port >/dev/null 2>&1
    fi
}

# Check common ports that might be in use
ports_to_check=(3000 3001 3002 3003)
available_port=3001

echo "🔍 Checking port availability..."

for port in "${ports_to_check[@]}"; do
    if check_port $port; then
        echo "❌ Port $port is in use"
    else
        echo "✅ Port $port is available"
        if [ $available_port -eq 3001 ] || [ $port -lt $available_port ]; then
            available_port=$port
        fi
    fi
done

echo
echo "📡 Recommended Grafana port: $available_port"

# If Grafana config exists, update it
if [ -f /etc/grafana/grafana.ini ]; then
    echo "🔧 Updating Grafana configuration..."
    sudo sed -i "s/^http_port = .*/http_port = $available_port/" /etc/grafana/grafana.ini
    sudo sed -i "s/^;http_port = .*/http_port = $available_port/" /etc/grafana/grafana.ini
    sudo sed -i "s/^#http_port = .*/http_port = $available_port/" /etc/grafana/grafana.ini
    
    # Also update the address to bind to all interfaces
    sudo sed -i "s/^;http_addr = .*/http_addr = 0.0.0.0/" /etc/grafana/grafana.ini
    sudo sed -i "s/^#http_addr = .*/http_addr = 0.0.0.0/" /etc/grafana/grafana.ini
    
    echo "✅ Grafana configured to use port $available_port"
    
    # Restart Grafana if it's running
    if systemctl is-active --quiet grafana-server; then
        echo "🔄 Restarting Grafana service..."
        sudo systemctl restart grafana-server
        sleep 3
        
        if systemctl is-active --quiet grafana-server; then
            echo "✅ Grafana restarted successfully"
        else
            echo "❌ Failed to restart Grafana"
        fi
    fi
else
    echo "ℹ️  Grafana not installed yet. Port $available_port will be configured during installation."
fi

echo
echo "🚀 Next steps:"
echo "1. Install Grafana: ./scripts/install_grafana.sh"
echo "2. Access Grafana: http://localhost:$available_port"
echo "3. Setup dashboards: python3 scripts/setup_grafana.py --url http://localhost:$available_port --password YOUR_PASSWORD"
echo
echo "🌐 Grafana will be accessible at: http://localhost:$available_port"