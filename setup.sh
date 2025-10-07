#!/bin/bash

# OpenProject DevLake Integration - Setup Script
# This script sets up the complete integration environment

set -e  # Exit on error

echo "=================================================="
echo "OpenProject DevLake Integration - Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Docker containers are running
echo "Step 1: Checking Docker containers..."
if docker ps | grep -q "devlake-docker-mysql"; then
    print_success "MySQL container is running"
else
    print_error "MySQL container is not running"
    echo "Please start your DevLake containers with: docker-compose up -d"
    exit 1
fi

if docker ps | grep -q "devlake-docker-devlake"; then
    print_success "DevLake container is running"
else
    print_error "DevLake container is not running"
    exit 1
fi

# Create directory structure
echo ""
echo "Step 2: Creating directory structure..."
mkdir -p schema
mkdir -p collectors
mkdir -p extractors
mkdir -p converters
mkdir -p grafana
mkdir -p logs
print_success "Directory structure created"

# Check if Python is installed
echo ""
echo "Step 3: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python is installed: $PYTHON_VERSION"
else
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Step 4: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Check configuration files
echo ""
echo "Step 5: Checking configuration files..."
if [ -f "config.yaml" ]; then
    print_success "config.yaml found"
    
    # Check if config has been updated
    if grep -q "your-openproject-instance.com" config.yaml; then
        print_error "Please update config.yaml with your OpenProject URL and API key"
        echo ""
        echo "Required changes in config.yaml:"
        echo "  1. Update 'base_url' with your OpenProject URL"
        echo "  2. Update 'api_key' with your OpenProject API key"
        echo ""
        echo "To get your API key:"
        echo "  1. Log in to OpenProject"
        echo "  2. Go to: Avatar → My Account → Access tokens"
        echo "  3. Create a new API token"
        echo "  4. Copy and paste it in config.yaml"
        exit 1
    fi
    print_success "config.yaml appears to be configured"
else
    print_error "config.yaml not found"
    exit 1
fi

# Test database connection
echo ""
echo "Step 6: Testing database connection..."
if [ -f "test_connection.py" ]; then
    python3 test_connection.py
    if [ $? -eq 0 ]; then
        print_success "All connection tests passed"
    else
        print_error "Connection tests failed. Please fix the issues above."
        exit 1
    fi
else
    print_error "test_connection.py not found"
    exit 1
fi

echo ""
echo "=================================================="
echo "Setup completed successfully!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Create database schema:"
echo "     python3 database_setup.py"
echo ""
echo "  2. Run initial data collection:"
echo "     python3 collectors/openproject_collector.py --verbose"
echo ""
echo "  3. Extract and transform data:"
echo "     python3 extractors/openproject_extractor.py"
echo "     python3 converters/openproject_converter.py"
echo ""
echo "  4. View data in Grafana:"
echo "     http://localhost:3002"
echo ""