#!/bin/bash

# OpenProject DevLake Grafana Installation Script
# This script installs Grafana and sets it up for OpenProject DevLake visualization

set -e

echo "🚀 Installing Grafana for OpenProject DevLake Integration"
echo "========================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   warning "This script should not be run as root for security reasons"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Function to install Grafana on Ubuntu/Debian
install_grafana_debian() {
    info "Installing Grafana on Ubuntu/Debian system..."
    
    # Add Grafana GPG key and repository
    sudo apt-get update
    sudo apt-get install -y software-properties-common wget
    
    # Add Grafana repository
    sudo mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
    
    # Install Grafana
    sudo apt-get update
    sudo apt-get install -y grafana
    
    success "Grafana installed successfully!"
}

# Function to install Grafana on RHEL/CentOS/Fedora
install_grafana_rhel() {
    info "Installing Grafana on RHEL/CentOS/Fedora system..."
    
    # Add Grafana repository
    sudo tee /etc/yum.repos.d/grafana.repo <<EOF
[grafana]
name=grafana
baseurl=https://rpm.grafana.com
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://rpm.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF
    
    # Install Grafana
    sudo yum install -y grafana
    
    success "Grafana installed successfully!"
}

# Detect OS and install accordingly
if [[ -f /etc/debian_version ]]; then
    install_grafana_debian
elif [[ -f /etc/redhat-release ]]; then
    install_grafana_rhel
else
    error "Unsupported operating system"
    echo "Please install Grafana manually: https://grafana.com/docs/grafana/latest/setup-grafana/installation/"
    exit 1
fi

# Enable and start Grafana service
info "Starting Grafana service..."
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Wait for Grafana to start
info "Waiting for Grafana to start..."
sleep 10

# Check if Grafana is running
if systemctl is-active --quiet grafana-server; then
    success "Grafana is running successfully!"
else
    error "Failed to start Grafana service"
    echo "Check logs with: sudo journalctl -u grafana-server"
    exit 1
fi

# Configure Grafana to use port 3001 to avoid conflicts
info "Configuring Grafana to use port 3001..."
sudo sed -i 's/;http_port = 3000/http_port = 3001/' /etc/grafana/grafana.ini
sudo sed -i 's/#http_port = 3000/http_port = 3001/' /etc/grafana/grafana.ini

# Restart Grafana with new configuration
sudo systemctl restart grafana-server
sleep 5

# Display access information
echo
echo "========================================================================"
success "Grafana Installation Complete!"
echo "========================================================================"
echo
echo "🌐 Access Grafana:"
echo "   URL: http://localhost:3001"
echo "   Username: admin"
echo "   Password: admin"
echo
warning "IMPORTANT: Change the default password on first login!"
echo
echo "🔧 Next Steps:"
echo "   1. Access Grafana in your browser"
echo "   2. Change the default password"
echo "   3. Run the dashboard setup script:"
echo "      python3 scripts/setup_grafana.py --url http://localhost:3001 --password YOUR_NEW_PASSWORD"
echo
echo "📊 Dashboard Setup:"
echo "   The setup script will create:"
echo "   - MySQL DevLake datasource"
echo "   - Team Productivity Dashboard"
echo "   - Sprint Progress Dashboard" 
echo "   - Issues Metrics & DORA Dashboard"
echo
echo "🔍 Monitoring:"
echo "   - Check service status: sudo systemctl status grafana-server"
echo "   - View logs: sudo journalctl -u grafana-server -f"
echo "   - Config file: /etc/grafana/grafana.ini"
echo
success "Installation completed successfully! 🎉"