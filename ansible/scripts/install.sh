#!/bin/bash

# FastAPI Xray VPN Service - Ansible Installation Script
# This script sets up the Ansible environment for deploying the VPN service

set -e

echo "🚀 FastAPI Xray VPN Service - Ansible Setup"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_status "Python version: $PYTHON_VERSION ✓"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip3 first."
    exit 1
fi

print_status "pip3 is available ✓"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python requirements
print_status "Installing Python requirements..."
pip install -r requirements.txt

# Install Ansible Galaxy requirements
print_status "Installing Ansible Galaxy requirements..."
ansible-galaxy install -r requirements.yml

# Check Ansible installation
print_status "Checking Ansible installation..."
ansible --version

# Create SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    print_warning "SSH key not found. Generating new SSH key..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    print_status "SSH key generated. Don't forget to add the public key to your servers!"
    print_status "Public key:"
    cat ~/.ssh/id_rsa.pub
fi

# Create backup directory
print_status "Creating backup directory..."
mkdir -p backups

# Set permissions
print_status "Setting proper permissions..."
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Test Ansible connectivity (if inventory is configured)
if [ -f "inventory/hosts.yml" ]; then
    print_status "Testing Ansible connectivity..."
    if ansible all -m ping --one-line 2>/dev/null; then
        print_status "Ansible connectivity test passed ✓"
    else
        print_warning "Ansible connectivity test failed. Please check your inventory configuration."
    fi
else
    print_warning "Inventory file not found. Please configure inventory/hosts.yml before running playbooks."
fi

print_status "Setup completed successfully! 🎉"
echo ""
echo "Next steps:"
echo "1. Configure inventory/hosts.yml with your server details"
echo "2. Update group_vars/ with your specific settings"
echo "3. Run: ansible-playbook playbooks/deploy.yml"
echo ""
echo "To activate the virtual environment in the future:"
echo "source venv/bin/activate"
