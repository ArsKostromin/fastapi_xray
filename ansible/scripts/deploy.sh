#!/bin/bash

# FastAPI Xray VPN Service - Deployment Script
# This script deploys the VPN service using Ansible

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}[HEADER]${NC} $1"
}

# Default values
PLAYBOOK="deploy.yml"
LIMIT=""
TAGS=""
DRY_RUN=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--playbook)
            PLAYBOOK="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        -t|--tags)
            TAGS="--tags $2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -p, --playbook PLAYBOOK    Playbook to run (default: deploy.yml)"
            echo "  -l, --limit HOSTS         Limit to specific hosts"
            echo "  -t, --tags TAGS           Run only tasks with specific tags"
            echo "  -d, --dry-run             Perform a dry run (check mode)"
            echo "  -v, --verbose             Verbose output"
            echo "  -h, --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Deploy all services"
            echo "  $0 -l vpn-server-1                   # Deploy to specific server"
            echo "  $0 -t docker,nginx                   # Deploy only Docker and Nginx"
            echo "  $0 -d                                # Dry run"
            echo "  $0 -p update.yml                     # Run update playbook"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_header "FastAPI Xray VPN Service - Deployment"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check if Ansible is available
if ! command -v ansible-playbook &> /dev/null; then
    print_error "ansible-playbook not found. Please run install.sh first."
    exit 1
fi

# Check if inventory file exists
if [ ! -f "inventory/hosts.yml" ]; then
    print_error "Inventory file not found. Please configure inventory/hosts.yml first."
    exit 1
fi

# Check if playbook exists
if [ ! -f "playbooks/$PLAYBOOK" ]; then
    print_error "Playbook not found: playbooks/$PLAYBOOK"
    exit 1
fi

# Build ansible-playbook command
ANSIBLE_CMD="ansible-playbook playbooks/$PLAYBOOK"

if [ -n "$LIMIT" ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD $LIMIT"
fi

if [ -n "$TAGS" ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD $TAGS"
fi

if [ "$DRY_RUN" = true ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --check"
    print_warning "Running in dry-run mode (no changes will be made)"
fi

if [ "$VERBOSE" = true ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -vvv"
fi

# Display configuration
print_status "Configuration:"
echo "  Playbook: $PLAYBOOK"
echo "  Limit: ${LIMIT:-'all hosts'}"
echo "  Tags: ${TAGS:-'all tasks'}"
echo "  Dry run: $DRY_RUN"
echo "  Verbose: $VERBOSE"
echo ""

# Confirm deployment
if [ "$DRY_RUN" = false ]; then
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled."
        exit 0
    fi
fi

# Run the playbook
print_status "Running Ansible playbook..."
echo "Command: $ANSIBLE_CMD"
echo ""

eval $ANSIBLE_CMD

# Check exit status
if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully! 🎉"
    
    if [ "$DRY_RUN" = false ]; then
        echo ""
        print_status "Next steps:"
        echo "1. Check service status: ansible vpn_servers -m systemd -a 'name=xray'"
        echo "2. View logs: ansible vpn_servers -m shell -a 'tail -f /opt/fastapi_xray/logs/xray/access.log'"
        echo "3. Test connectivity: curl -k https://your-domain/health"
    fi
else
    print_error "Deployment failed! Please check the output above for errors."
    exit 1
fi
