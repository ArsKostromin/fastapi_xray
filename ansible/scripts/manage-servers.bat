@echo off
setlocal enabledelayedexpansion

REM FastAPI Xray VPN Service - Windows Server Management Script
REM This script helps manage multiple VPN servers from Windows

echo 🚀 FastAPI Xray VPN Service - Server Management
echo ================================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run install-windows.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if Ansible is available
ansible-playbook --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ansible-playbook not found. Please run install-windows.bat first.
    pause
    exit /b 1
)

REM Default values
set ACTION=
set LIMIT=
set TAGS=
set DRY_RUN=false
set VERBOSE=false
set COMPOSE_ACTION=up
set BUILD=false

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :execute_action
if "%~1"=="-a" (
    set ACTION=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--action" (
    set ACTION=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-l" (
    set LIMIT=--limit %~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--limit" (
    set LIMIT=--limit %~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-t" (
    set TAGS=--tags %~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--tags" (
    set TAGS=--tags %~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-d" (
    set DRY_RUN=true
    shift
    goto :parse_args
)
if "%~1"=="--dry-run" (
    set DRY_RUN=true
    shift
    goto :parse_args
)
if "%~1"=="-v" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if "%~1"=="-c" (
    set COMPOSE_ACTION=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--compose-action" (
    set COMPOSE_ACTION=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-b" (
    set BUILD=true
    shift
    goto :parse_args
)
if "%~1"=="--build" (
    set BUILD=true
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
echo [ERROR] Unknown option: %~1
goto :show_help

:show_help
echo.
echo Usage: %0 [OPTIONS]
echo.
echo Actions:
echo   check           Check connectivity to all servers
echo   deploy          Deploy to all servers
echo   update          Update all servers
echo   backup          Backup all servers
echo   status          Check status of all servers
echo   logs            View logs from all servers
echo   restart         Restart services on all servers
echo   compose         Manage Docker Compose services
echo.
echo Options:
echo   -a, --action ACTION     Action to perform
echo   -l, --limit SERVER      Limit to specific server
echo   -t, --tags TAGS         Run only tasks with specific tags
echo   -d, --dry-run           Perform a dry run (check mode)
echo   -v, --verbose           Verbose output
echo   -c, --compose-action    Docker Compose action (up, down, restart, status, logs)
echo   -b, --build             Build images before starting (for compose action)
echo   -h, --help              Show this help message
echo.
echo Examples:
echo   %0 -a check                                    # Check all servers
echo   %0 -a deploy                                   # Deploy to all servers
echo   %0 -a deploy -l uae-server                     # Deploy to UAE server only
echo   %0 -a deploy -t docker,nginx                   # Deploy only Docker and Nginx
echo   %0 -a status                                   # Check status of all servers
echo   %0 -a logs                                     # View logs from all servers
echo   %0 -a compose -c up -b                         # Start Docker Compose with build
echo   %0 -a compose -c down                          # Stop Docker Compose services
echo   %0 -a compose -c status                        # Show Docker Compose status
echo.
echo Available servers:
echo   uae-server (UAE) - 176.97.67.100
echo   brazil-server (Brazil) - 38.180.220.125
echo   germany-server (Germany) - 37.1.199.23
echo   japan-server (Japan) - 176.97.71.56
echo   turkey-server (Turkey) - 5.180.45.191
echo   spain-server (Spain) - 45.12.150.217
echo   australia-server (Australia) - 45.15.185.58
echo   usa-server (USA) - 94.131.101.213
echo.
pause
exit /b 0

:execute_action
if "%ACTION%"=="" (
    echo [ERROR] No action specified. Use -a or --action parameter.
    goto :show_help
)

echo [INFO] Available VPN Servers:
echo   uae-server (UAE) - 176.97.67.100
echo   brazil-server (Brazil) - 38.180.220.125
echo   germany-server (Germany) - 37.1.199.23
echo   japan-server (Japan) - 176.97.71.56
echo   turkey-server (Turkey) - 5.180.45.191
echo   spain-server (Spain) - 45.12.150.217
echo   australia-server (Australia) - 45.15.185.58
echo   usa-server (USA) - 94.131.101.213
echo.

if "%ACTION%"=="check" goto :check_connectivity
if "%ACTION%"=="deploy" goto :deploy_all
if "%ACTION%"=="update" goto :update_all
if "%ACTION%"=="backup" goto :backup_all
if "%ACTION%"=="status" goto :check_status
if "%ACTION%"=="logs" goto :view_logs
if "%ACTION%"=="restart" goto :restart_services
if "%ACTION%"=="compose" goto :manage_compose
echo [ERROR] Unknown action: %ACTION%
goto :show_help

:check_connectivity
echo [INFO] Checking connectivity to all servers...
ansible-playbook playbooks/check-connectivity.yml
goto :end

:deploy_all
echo [INFO] Deploying to all servers...
if "%DRY_RUN%"=="true" (
    echo [WARNING] Running in dry-run mode (no changes will be made)
    ansible-playbook playbooks/deploy-no-ssl.yml --check %LIMIT% %TAGS%
) else (
    ansible-playbook playbooks/deploy-no-ssl.yml %LIMIT% %TAGS%
)
goto :end

:update_all
echo [INFO] Updating all servers...
ansible-playbook playbooks/update.yml %LIMIT% %TAGS%
goto :end

:backup_all
echo [INFO] Backing up all servers...
ansible-playbook playbooks/backup.yml %LIMIT% %TAGS%
goto :end

:check_status
echo [INFO] Checking status of all servers...
ansible vpn_servers -m systemd -a "name=xray" %LIMIT%
ansible vpn_servers -m systemd -a "name=fastapi" %LIMIT%
ansible vpn_servers -m systemd -a "name=squid" %LIMIT%
ansible vpn_servers -m systemd -a "name=nginx" %LIMIT%
goto :end

:view_logs
echo [INFO] Viewing logs from all servers...
echo Xray logs:
ansible vpn_servers -m shell -a "tail -n 20 /opt/fastapi_xray/logs/xray/access.log" %LIMIT%
echo.
echo FastAPI logs:
ansible vpn_servers -m shell -a "docker logs fastapi --tail 20" %LIMIT%
echo.
echo Nginx logs:
ansible vpn_servers -m shell -a "tail -n 20 /var/log/nginx/fastapi_access.log" %LIMIT%
goto :end

:restart_services
echo [INFO] Restarting services on all servers...
ansible vpn_servers -m systemd -a "name=xray state=restarted" %LIMIT%
ansible vpn_servers -m systemd -a "name=fastapi state=restarted" %LIMIT%
ansible vpn_servers -m systemd -a "name=squid state=restarted" %LIMIT%
ansible vpn_servers -m systemd -a "name=nginx state=restarted" %LIMIT%
goto :end

:manage_compose
echo [INFO] Managing Docker Compose services...
set COMPOSE_VARS=
if "%BUILD%"=="true" set COMPOSE_VARS=-e build=true
ansible-playbook playbooks/docker-compose.yml %LIMIT% %TAGS% -e "action=%COMPOSE_ACTION%" %COMPOSE_VARS%
goto :end

:end
echo.
echo [SUCCESS] Operation completed successfully! 🎉
pause
