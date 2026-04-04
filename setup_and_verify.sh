#!/bin/bash
#
# NFS Benchmark Suite - Setup and Verification Script
# This script installs prerequisites and verifies the environment
#
# Usage:
#   ./setup_and_verify.sh              # Interactive mode
#   ./setup_and_verify.sh --auto       # Automatic installation (requires sudo)
#   ./setup_and_verify.sh --check-only # Only check, don't install

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
AUTO_INSTALL=false
CHECK_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --auto)
            AUTO_INSTALL=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auto        Automatic installation (requires sudo)"
            echo "  --check-only  Only check prerequisites, don't install"
            echo "  --help        Show this help message"
            exit 0
            ;;
    esac
done

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NFS Benchmark Suite${NC}"
echo -e "${BLUE}Setup and Verification Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="rhel"
    elif [ -f /etc/debian_version ]; then
        OS="debian"
    else
        OS="unknown"
    fi
    
    echo -e "${BLUE}Detected OS:${NC} $OS $OS_VERSION"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    echo -e "\n${YELLOW}Checking Python...${NC}"
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 6 ]; then
            echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
            return 0
        else
            echo -e "${RED}✗ Python 3.6+ required, found $PYTHON_VERSION${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Python 3 not found${NC}"
        return 1
    fi
}

# Check pip
check_pip() {
    echo -e "\n${YELLOW}Checking pip...${NC}"
    
    if command_exists pip3; then
        PIP_VERSION=$(pip3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓ pip $PIP_VERSION found${NC}"
        return 0
    elif command_exists pip; then
        PIP_VERSION=$(pip --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓ pip $PIP_VERSION found${NC}"
        return 0
    else
        echo -e "${RED}✗ pip not found${NC}"
        return 1
    fi
}

# Check dd command
check_dd() {
    echo -e "\n${YELLOW}Checking dd command...${NC}"
    
    if command_exists dd; then
        echo -e "${GREEN}✓ dd command found${NC}"
        return 0
    else
        echo -e "${RED}✗ dd command not found${NC}"
        return 1
    fi
}

# Check fio
check_fio() {
    echo -e "\n${YELLOW}Checking fio...${NC}"
    
    if command_exists fio; then
        FIO_VERSION=$(fio --version 2>&1)
        echo -e "${GREEN}✓ fio $FIO_VERSION found${NC}"
        return 0
    else
        echo -e "${RED}✗ fio not found${NC}"
        return 1
    fi
}

# Check iozone
check_iozone() {
    echo -e "\n${YELLOW}Checking iozone...${NC}"
    
    if command_exists iozone; then
        IOZONE_VERSION=$(iozone -v 2>&1 | head -n 1 || echo "version unknown")
        echo -e "${GREEN}✓ iozone found ($IOZONE_VERSION)${NC}"
        return 0
    else
        echo -e "${RED}✗ iozone not found${NC}"
        return 1
    fi
}

# Check bonnie++
check_bonnie() {
    echo -e "\n${YELLOW}Checking bonnie++...${NC}"
    
    if command_exists bonnie++; then
        BONNIE_VERSION=$(bonnie++ -h 2>&1 | head -n 1 || echo "version unknown")
        echo -e "${GREEN}✓ bonnie++ found${NC}"
        return 0
    else
        echo -e "${RED}✗ bonnie++ not found${NC}"
        return 1
    fi
}

# Check dbench
check_dbench() {
    echo -e "\n${YELLOW}Checking dbench...${NC}"
    
    if command_exists dbench; then
        DBENCH_VERSION=$(dbench --version 2>&1 | head -n 1 || echo "version unknown")
        echo -e "${GREEN}✓ dbench found ($DBENCH_VERSION)${NC}"
        return 0
    else
        echo -e "${RED}✗ dbench not found${NC}"
        return 1
    fi
}

# Check nfsstat (optional)
check_nfsstat() {
    echo -e "\n${YELLOW}Checking nfsstat (optional)...${NC}"
    
    if command_exists nfsstat; then
        echo -e "${GREEN}✓ nfsstat found${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ nfsstat not found (NFS stats collection will be disabled)${NC}"
        return 1
    fi
}

# Check Python dependencies
check_python_deps() {
    echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
    
    local missing_deps=()
    
    # Check PyYAML
    if python3 -c "import yaml" 2>/dev/null; then
        echo -e "${GREEN}✓ PyYAML found${NC}"
    else
        echo -e "${RED}✗ PyYAML not found${NC}"
        missing_deps+=("pyyaml")
    fi
    
    # Check psutil (optional)
    if python3 -c "import psutil" 2>/dev/null; then
        echo -e "${GREEN}✓ psutil found${NC}"
    else
        echo -e "${YELLOW}⚠ psutil not found (system metrics will be disabled)${NC}"
        missing_deps+=("psutil")
    fi
    
    # Check plotly (optional)
    if python3 -c "import plotly" 2>/dev/null; then
        echo -e "${GREEN}✓ plotly found${NC}"
    else
        echo -e "${YELLOW}⚠ plotly not found (HTML reports will be disabled)${NC}"
        missing_deps+=("plotly")
    fi
    
    # Check jinja2 (optional)
    if python3 -c "import jinja2" 2>/dev/null; then
        echo -e "${GREEN}✓ jinja2 found${NC}"
    else
        echo -e "${YELLOW}⚠ jinja2 not found (HTML reports will be disabled)${NC}"
        missing_deps+=("jinja2")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        return 0
    else
        echo -e "${YELLOW}Missing Python dependencies: ${missing_deps[*]}${NC}"
        return 1
    fi
}

# Install system packages
install_system_packages() {
    echo -e "\n${YELLOW}Installing system packages...${NC}"
    
    case $OS in
        ubuntu|debian)
            if [ "$AUTO_INSTALL" = true ]; then
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip fio iozone3 bonnie++ dbench nfs-common
            else
                echo "Run the following commands to install system packages:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install -y python3 python3-pip fio iozone3 bonnie++ dbench nfs-common"
            fi
            ;;
        rhel|centos|fedora)
            if [ "$AUTO_INSTALL" = true ]; then
                # Install core packages first
                if command_exists dnf; then
                    echo "Installing core packages..."
                    sudo dnf install -y python3 python3-pip fio nfs-utils
                    
                    # Try to install optional benchmark tools (may not be available)
                    echo "Attempting to install optional benchmark tools..."
                    sudo dnf install -y iozone3 2>/dev/null || echo -e "${YELLOW}⚠ iozone3 not available in repos${NC}"
                    sudo dnf install -y dbench 2>/dev/null || echo -e "${YELLOW}⚠ dbench not available in repos${NC}"
                    sudo dnf install -y bonnie++ 2>/dev/null || echo -e "${YELLOW}⚠ bonnie++ not available in repos${NC}"
                else
                    echo "Installing core packages..."
                    sudo yum install -y python3 python3-pip fio nfs-utils
                    
                    # Try to install optional benchmark tools (may not be available)
                    echo "Attempting to install optional benchmark tools..."
                    sudo yum install -y iozone3 2>/dev/null || echo -e "${YELLOW}⚠ iozone3 not available in repos${NC}"
                    sudo yum install -y dbench 2>/dev/null || echo -e "${YELLOW}⚠ dbench not available in repos${NC}"
                    sudo yum install -y bonnie++ 2>/dev/null || echo -e "${YELLOW}⚠ bonnie++ not available in repos${NC}"
                fi
                echo -e "${YELLOW}Note: Some benchmark tools may need manual installation from source or EPEL${NC}"
            else
                echo "Run the following commands to install system packages:"
                if command_exists dnf; then
                    echo "  sudo dnf install -y python3 python3-pip fio nfs-utils"
                    echo "  # Optional benchmark tools (may not be available):"
                    echo "  sudo dnf install -y iozone3 dbench bonnie++"
                else
                    echo "  sudo yum install -y python3 python3-pip fio nfs-utils"
                    echo "  # Optional benchmark tools (may not be available):"
                    echo "  sudo yum install -y iozone3 dbench bonnie++"
                fi
            fi
            ;;
        *)
            echo -e "${YELLOW}Unknown OS. Please install manually:${NC}"
            echo "  - Python 3.7+"
            echo "  - pip"
            echo "  - fio"
            echo "  - iozone3"
            echo "  - bonnie++"
            echo "  - dbench"
            echo "  - NFS client utilities"
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
    
    if [ -f "requirements.txt" ]; then
        if [ "$AUTO_INSTALL" = true ]; then
            pip3 install -r requirements.txt
        else
            echo "Run the following command to install Python dependencies:"
            echo "  pip3 install -r requirements.txt"
        fi
    else
        echo -e "${YELLOW}requirements.txt not found. Installing core dependencies...${NC}"
        if [ "$AUTO_INSTALL" = true ]; then
            pip3 install pyyaml psutil plotly jinja2
        else
            echo "Run the following command to install Python dependencies:"
            echo "  pip3 install pyyaml psutil plotly jinja2"
        fi
    fi
}

# Test basic functionality
test_functionality() {
    echo -e "\n${YELLOW}Testing basic functionality...${NC}"
    
    # Test Python script syntax
    if python3 -m py_compile runtest.py 2>/dev/null; then
        echo -e "${GREEN}✓ Python script syntax OK${NC}"
    else
        echo -e "${RED}✗ Python script has syntax errors${NC}"
        return 1
    fi
    
    # Test help command (allow warnings on stderr)
    if python3 runtest.py --help >/dev/null; then
        echo -e "${GREEN}✓ Script help command works${NC}"
    else
        echo -e "${RED}✗ Script help command failed${NC}"
        return 1
    fi
    
    # Test configuration loading
    if [ -f "test_config.yaml" ]; then
        if python3 -c "
import yaml
with open('test_config.yaml', 'r') as f:
    yaml.safe_load(f)
print('Configuration file is valid')
" 2>/dev/null; then
            echo -e "${GREEN}✓ Configuration file is valid${NC}"
        else
            echo -e "${RED}✗ Configuration file has errors${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ test_config.yaml not found${NC}"
    fi
    
    return 0
}

# Main execution
main() {
    detect_os
    
    echo -e "\n${BLUE}=== CHECKING PREREQUISITES ===${NC}"
    
    local checks_failed=0
    
    check_python || checks_failed=$((checks_failed + 1))
    check_pip || checks_failed=$((checks_failed + 1))
    check_dd || checks_failed=$((checks_failed + 1))
    check_fio || checks_failed=$((checks_failed + 1))
    check_iozone || checks_failed=$((checks_failed + 1))
    check_bonnie || checks_failed=$((checks_failed + 1))
    check_dbench || checks_failed=$((checks_failed + 1))
    check_nfsstat  # Optional, don't count failures
    check_python_deps || checks_failed=$((checks_failed + 1))
    
    if [ "$CHECK_ONLY" = true ]; then
        echo -e "\n${BLUE}=== CHECK COMPLETE ===${NC}"
        if [ $checks_failed -eq 0 ]; then
            echo -e "${GREEN}All prerequisites are satisfied!${NC}"
            exit 0
        else
            echo -e "${RED}$checks_failed prerequisite(s) missing${NC}"
            exit 1
        fi
    fi
    
    if [ $checks_failed -gt 0 ]; then
        echo -e "\n${BLUE}=== INSTALLING MISSING PREREQUISITES ===${NC}"
        
        if [ "$AUTO_INSTALL" = false ]; then
            echo -e "${YELLOW}Some prerequisites are missing. Install them? (y/N)${NC}"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                echo "Installation cancelled."
                exit 1
            fi
        fi
        
        install_system_packages
        install_python_deps
        
        echo -e "\n${BLUE}=== RE-CHECKING AFTER INSTALLATION ===${NC}"
        checks_failed=0
        check_python || checks_failed=$((checks_failed + 1))
        check_pip || checks_failed=$((checks_failed + 1))
        check_dd || checks_failed=$((checks_failed + 1))
        check_fio || checks_failed=$((checks_failed + 1))
        check_iozone || checks_failed=$((checks_failed + 1))
        check_bonnie || checks_failed=$((checks_failed + 1))
        check_dbench || checks_failed=$((checks_failed + 1))
        check_python_deps || checks_failed=$((checks_failed + 1))
    fi
    
    echo -e "\n${BLUE}=== TESTING FUNCTIONALITY ===${NC}"
    if test_functionality; then
        echo -e "\n${GREEN}=== SETUP COMPLETE ===${NC}"
        echo -e "${GREEN}NFS Benchmark Suite is ready to use!${NC}"
        echo ""
        echo "Usage examples:"
        echo "  python3 runtest.py --mount-path /mnt/nfs1 --quick-test"
        echo "  python3 runtest.py --mount-path /mnt/nfs1 --config custom_config.yaml"
        echo ""
        echo "For more options, run:"
        echo "  python3 runtest.py --help"
    else
        echo -e "\n${RED}=== SETUP FAILED ===${NC}"
        echo -e "${RED}Some functionality tests failed. Please check the errors above.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"

# Made with Bob
