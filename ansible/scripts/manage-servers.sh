#!/bin/bash

# FastAPI Xray VPN Service - Server Management Script
# This script helps manage multiple VPN servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_server() {
    echo -e "${CYAN}[SERVER]${NC} $1"
}

# Server list
SERVERS=(
    "uae-server:UAE:176.97.67.100"
    "brazil-server:Brazil:38.180.220.125"
    "germany-server:Germany:37.1.199.23"
    "japan-server:Japan:176.97.71.56"
    "turkey-server:Turkey:5.180.45.191"
    "spain-server:Spain:45.12.150.217"
    "australia-server:Australia:45.15.185.58"
    "usa-server:USA:94.131.101.213"
)

# Default values
PLAYBOOK=""
LIMIT=""
TAGS=""
DRY_RUN=false
VERBOSE=false
ACTION=""
COMPOSE_ACTION="up"
BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
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
        -c|--compose-action)
            COMPOSE_ACTION="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

show_help() {
    echo "FastAPI Xray VPN Service - Server Management"
    echo "============================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Actions:"
    echo "  check           Check connectivity to all servers"
    echo "  deploy          Deploy to all servers"
    echo "  update          Update all servers"
    echo "  backup          Backup all servers"
    echo "  status          Check status of all servers"
    echo "  logs            View logs from all servers"
    echo "  restart         Restart services on all servers"
    echo "  compose         Manage Docker Compose services"
    echo ""
    echo "Options:"
    echo "  -a, --action ACTION     Action to perform"
    echo "  -p, --playbook PLAYBOOK Playbook to run"
    echo "  -l, --limit SERVER      Limit to specific server"
    echo "  -t, --tags TAGS         Run only tasks with specific tags"
    echo "  -d, --dry-run           Perform a dry run (check mode)"
    echo "  -v, --verbose           Verbose output"
    echo "  -c, --compose-action    Docker Compose action (up, down, restart, status, logs)"
    echo "  -b, --build             Build images before starting (for compose action)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -a check                                    # Check all servers"
    echo "  $0 -a deploy                                   # Deploy to all servers"
    echo "  $0 -a deploy -l uae-server                     # Deploy to UAE server only"
    echo "  $0 -a deploy -t docker,nginx                   # Deploy only Docker and Nginx"
    echo "  $0 -a status                                   # Check status of all servers"
    echo "  $0 -a logs                                     # View logs from all servers"
    echo "  $0 -a compose -c up -b                         # Start Docker Compose with build"
    echo "  $0 -a compose -c down                          # Stop Docker Compose services"
    echo "  $0 -a compose -c status                        # Show Docker Compose status"
    echo ""
    echo "Available servers:"
    for server_info in "${SERVERS[@]}"; do
        IFS=':' read -r name country ip <<< "$server_info"
        echo "  $name ($country) - $ip"
    done
}

show_server_list() {
    print_header "Available VPN Servers"
    echo "=========================="
    for server_info in "${SERVERS[@]}"; do
        IFS=':' read -r name country ip <<< "$server_info"
        print_server "$name ($country) - $ip"
    done
    echo ""
}

check_connectivity() {
    print_header "Checking connectivity to all servers..."
    ansible-playbook playbooks/check-connectivity.yml
}

deploy_all() {
    print_header "Deploying to all servers..."
    if [ "$DRY_RUN" = true ]; then
        print_warning "Running in dry-run mode (no changes will be made)"
        ansible-playbook playbooks/deploy-no-ssl.yml --check $LIMIT $TAGS
    else
        ansible-playbook playbooks/deploy-no-ssl.yml $LIMIT $TAGS
    fi
}

update_all() {
    print_header "Updating all servers..."
    ansible-playbook playbooks/update.yml $LIMIT $TAGS
}

backup_all() {
    print_header "Backing up all servers..."
    ansible-playbook playbooks/backup.yml $LIMIT $TAGS
}

check_status() {
    print_header "Checking status of all servers..."
    ansible vpn_servers -m systemd -a "name=xray" $LIMIT
    ansible vpn_servers -m systemd -a "name=fastapi" $LIMIT
    ansible vpn_servers -m systemd -a "name=squid" $LIMIT
    ansible vpn_servers -m systemd -a "name=nginx" $LIMIT
}

view_logs() {
    print_header "Viewing logs from all servers..."
    echo "Xray logs:"
    ansible vpn_servers -m shell -a "tail -n 20 /opt/fastapi_xray/logs/xray/access.log" $LIMIT
    echo ""
    echo "FastAPI logs:"
    ansible vpn_servers -m shell -a "docker logs fastapi --tail 20" $LIMIT
    echo ""
    echo "Nginx logs:"
    ansible vpn_servers -m shell -a "tail -n 20 /var/log/nginx/fastapi_access.log" $LIMIT
}

restart_services() {
    print_header "Restarting services on all servers..."
    ansible vpn_servers -m systemd -a "name=xray state=restarted" $LIMIT
    ansible vpn_servers -m systemd -a "name=fastapi state=restarted" $LIMIT
    ansible vpn_servers -m systemd -a "name=squid state=restarted" $LIMIT
    ansible vpn_servers -m systemd -a "name=nginx state=restarted" $LIMIT
}

manage_compose() {
    print_header "Managing Docker Compose services..."
    local compose_vars=""
    
    if [ "$BUILD" = true ]; then
        compose_vars="-e build=true"
    fi
    
    ansible-playbook playbooks/docker-compose.yml $LIMIT $TAGS -e "action=$COMPOSE_ACTION" $compose_vars
}

# Main execution
print_header "FastAPI Xray VPN Service - Server Management"
echo "=================================================="

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

# Show server list
show_server_list

# Execute action based on parameter
case $ACTION in
    "check")
        check_connectivity
        ;;
    "deploy")
        deploy_all
        ;;
    "update")
        update_all
        ;;
    "backup")
        backup_all
        ;;
    "status")
        check_status
        ;;
    "logs")
        view_logs
        ;;
    "restart")
        restart_services
        ;;
    "compose")
        manage_compose
        ;;
    "")
        print_error "No action specified. Use -a or --action parameter."
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown action: $ACTION"
        show_help
        exit 1
        ;;
esac

print_success "Operation completed successfully! 🎉"
