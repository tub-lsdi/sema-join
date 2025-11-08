#!/bin/bash

set -e
source load_env.sh
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DB_NAME="${DB_PATH:-corpus.db}"

# Log functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_header() {
    echo -e "\n${MAGENTA}═══════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════${NC}\n"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command_exists uv; then
        missing_deps+=("uv (Python package manager)")
    fi
    
    if ! command_exists node; then
        missing_deps+=("node (JavaScript runtime)")
    fi
    
    if ! command_exists npm; then
        missing_deps+=("npm (Node package manager)")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        log_info "Installation instructions:"
        echo "  • uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  • node/npm: https://nodejs.org/ or use nvm"
        return 1
    fi
    
    return 0
}

# Install backend dependencies
install_backend() {
    log_header "Installing Backend Dependencies"
    
    if ! command_exists uv; then
        log_error "uv is not installed. Please install it first:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    log_info "Installing Python dependencies with uv..."
    uv sync --extra backend
    
    log_success "Backend dependencies installed successfully!"
}

# Install frontend dependencies
install_frontend() {
    log_header "Installing Frontend Dependencies"
    
    if ! command_exists npm; then
        log_error "npm is not installed. Please install Node.js and npm first."
        return 1
    fi
    
    cd "$FRONTEND_DIR"
    
    log_info "Installing Node.js dependencies..."
    npm install
    
    log_success "Frontend dependencies installed successfully!"
}

# Install both
install_all() {
    log_header "Installing All Dependencies"
    
    install_backend
    echo ""
    install_frontend
    
    log_success "All dependencies installed successfully!"
}

# Run backend
run_backend() {
    log_header "Starting Backend Server"
    
    cd "$PROJECT_ROOT"
    
    if [ ! -f "$PROJECT_ROOT/$DB_NAME" ]; then
        log_warning "Database not found at $PROJECT_ROOT/corpus.db"
        log_info "You may need to run the setup script first:"
        echo "  ./backend/setup_database.sh"
        echo ""
    fi
    
    log_info "Starting FastAPI server on http://localhost:8000"
    log_info "API docs available at: http://localhost:8000/docs"
    log_info "Press CTRL+C to stop the server"
    echo ""
    
    uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
}

# Run frontend
run_frontend() {
    log_header "Starting Frontend Development Server"
    
    cd "$FRONTEND_DIR"
    
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_warning "node_modules not found. Installing dependencies first..."
        npm install
        echo ""
    fi
    
    log_info "Starting Next.js development server on http://localhost:3000"
    log_info "Press CTRL+C to stop the server"
    echo ""
    
    npm run dev
}

# Run both backend and frontend
run_both() {
    log_header "Starting Backend and Frontend Servers"
    
    # Check if dependencies are installed
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_warning "Frontend dependencies not found. Installing..."
        install_frontend
        echo ""
    fi
    
    log_info "Starting both servers..."
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:3000"
    log_info "Press CTRL+C to stop both servers"
    echo ""
    
    # Create a trap to kill both processes on exit
    trap 'kill $(jobs -p) 2>/dev/null' EXIT
    
    # Start backend in background
    cd "$PROJECT_ROOT"
    uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # Wait a bit for backend to start
    sleep 2
    
    # Start frontend in background
    cd "$FRONTEND_DIR"
    npm run dev &
    FRONTEND_PID=$!
    
    # Show process IDs
    log_success "Backend started (PID: $BACKEND_PID)"
    log_success "Frontend started (PID: $FRONTEND_PID)"
    echo ""
    log_info "Monitoring servers... (Press CTRL+C to stop)"
    
    # Wait for both processes
    wait
}

# Setup database
setup_database() {
    log_header "Setting Up Database"
    
    if [ -f "$BACKEND_DIR/setup_database.sh" ]; then
        cd "$BACKEND_DIR"
        bash setup_database.sh
    else
        log_error "setup_database.sh not found in backend directory"
        return 1
    fi
}

# Run tests
run_tests() {
    log_header "Running Tests"
    
    cd "$PROJECT_ROOT"
    
    # Check if tests directory exists
    if [ ! -d "$BACKEND_DIR/tests" ]; then
        log_error "Tests directory not found: backend/tests"
        return 1
    fi
    
    log_info "Running backend tests..."
    echo ""
    
    # Run all tests in backend/tests directory using unittest
    uv run python -m unittest discover -s "$BACKEND_DIR/tests" -p "test_*.py" -v
    
    if [ $? -eq 0 ]; then
        echo ""
        log_success "All tests passed!"
    else
        echo ""
        log_error "Some tests failed"
        return 1
    fi
}

# AI-related functions
ai_setup() {
    log_header "Setting Up AI (Ollama + Mistral)"
    
    # Check if Ollama is already installed
    if command_exists ollama; then
        log_success "Ollama is already installed"
        OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
        echo "  Version: $OLLAMA_VERSION"
        echo ""
    else
        log_info "Installing Ollama..."
        echo ""
        
        # Detect OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            log_info "Detected Linux. Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            log_info "Detected macOS. Installing Ollama..."
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            log_error "Unsupported OS. Please install Ollama manually from:"
            echo "  https://ollama.ai"
            return 1
        fi
        
        log_success "Ollama installed successfully!"
        echo ""
    fi
    
    # Pull Mistral model
    log_info "Pulling Mistral model (this may take a few minutes, ~4GB download)..."
    echo ""
    
    if ollama pull mistral; then
        log_success "Mistral model downloaded successfully!"
        echo ""
        
        log_success "AI setup complete!"
        echo ""
        log_info "Next steps:"
        echo "  1. Start Ollama: ./sema-join.sh ai serve"
        echo "  2. Start backend: ./sema-join.sh run backend"
        echo "  3. Start frontend: ./sema-join.sh run frontend"
        echo ""
    else
        log_error "Failed to pull Mistral model"
        return 1
    fi
}

ai_status() {
    log_header "AI Status"
    
    echo "🤖 Ollama Status:"
    echo ""
    
    # Check if Ollama is installed
    if command_exists ollama; then
        OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
        log_success "Ollama installed: $OLLAMA_VERSION"
    else
        log_error "Ollama not installed"
        echo ""
        log_info "Install with: ./sema-join.sh ai setup"
        return 1
    fi
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        log_success "Ollama service is running on http://localhost:11434"
        
        # Get list of models
        echo ""
        log_info "Checking for Mistral model..."
        
        if ollama list 2>/dev/null | grep -q "mistral"; then
            log_success "Mistral model is available"
        else
            log_warning "Mistral model not found"
            echo ""
            log_info "Pull model with: ollama pull mistral"
        fi
    else
        log_warning "Ollama service is not running"
        echo ""
        log_info "Start with: ./sema-join.sh ai serve"
    fi
    
    echo ""
}

ai_serve() {
    log_header "Starting Ollama Service"
    
    if ! command_exists ollama; then
        log_error "Ollama is not installed"
        echo ""
        log_info "Install with: ./sema-join.sh ai setup"
        return 1
    fi
    
    # Check if already running
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        log_warning "Ollama is already running on http://localhost:11434"
        return 0
    fi
    
    log_info "Starting Ollama on http://localhost:11434"
    log_info "Press CTRL+C to stop the service"
    echo ""
    
    ollama serve
}

# Show project status
show_status() {
    log_header "Project Status"
    
    echo "📦 Dependencies:"
    echo ""
    
    # Check uv
    if command_exists uv; then
        UV_VERSION=$(uv --version 2>/dev/null || echo "unknown")
        log_success "uv: $UV_VERSION"
    else
        log_error "uv: not installed"
    fi
    
    # Check node
    if command_exists node; then
        NODE_VERSION=$(node --version)
        log_success "node: $NODE_VERSION"
    else
        log_error "node: not installed"
    fi
    
    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        log_success "npm: v$NPM_VERSION"
    else
        log_error "npm: not installed"
    fi
    
    # Check Ollama
    if command_exists ollama; then
        OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
        log_success "ollama: $OLLAMA_VERSION"
        
        # Check if running
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log_success "  → Service running ✓"
        else
            log_warning "  → Service not running (start with: ./sema-join.sh ai serve)"
        fi
    else
        log_warning "ollama: not installed (optional, for AI features)"
    fi
    
    echo ""
    echo "📁 Project Structure:"
    echo ""
    
    # Check backend
    if [ -d "$BACKEND_DIR" ]; then
        log_success "Backend directory exists"
        if [ -f "$PROJECT_ROOT/.venv/bin/python" ] || [ -f "$PROJECT_ROOT/.venv/Scripts/python" ]; then
            log_success "Python virtual environment exists"
        else
            log_warning "Python virtual environment not found"
        fi
    else
        log_error "Backend directory not found"
    fi
    
    # Check frontend
    if [ -d "$FRONTEND_DIR" ]; then
        log_success "Frontend directory exists"
        if [ -d "$FRONTEND_DIR/node_modules" ]; then
            log_success "Node modules installed"
        else
            log_warning "Node modules not found"
        fi
    else
        log_error "Frontend directory not found"
    fi
    
    # Check database
    if [ -f "$PROJECT_ROOT/corpus.db" ]; then
        DB_SIZE=$(du -h "$PROJECT_ROOT/corpus.db" | cut -f1)
        log_success "Database exists ($DB_SIZE)"
    else
        log_warning "Database not found (run setup)"
    fi
    
    echo ""
}

# Display help
show_help() {
    echo -e "${CYAN}SEMA-JOIN Project${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./sema-join.sh [command]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}install${NC} <target>"
    echo "    backend          Install backend dependencies (Python/uv)"
    echo "    frontend         Install frontend dependencies (Node.js/npm)"
    echo "    all              Install all dependencies"
    echo ""
    echo -e "  ${GREEN}run${NC} [target]"
    echo "    (no args)        Start both servers simultaneously"
    echo "    backend          Start backend server only (http://localhost:8000)"
    echo "    frontend         Start frontend server only (http://localhost:3000)"
    echo ""
    echo -e "  ${GREEN}db${NC}"
    echo "                     Setup and initialize the database"
    echo ""
    echo -e "  ${GREEN}tests${NC}"
    echo "                     Run tests"
    echo ""
    echo -e "  ${GREEN}status${NC}"
    echo "                     Show project status and dependencies"
    echo ""
    echo -e "  ${GREEN}ai${NC} <command>"
    echo "    setup            Install Ollama and pull Mistral model"
    echo "    status           Check AI status"
    echo "    serve            Start Ollama service"
    echo ""
    echo -e "  ${GREEN}help${NC}"
    echo "                     Show this help message"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  1. ./sema-join.sh install all"
    echo "  2. ./sema-join.sh db"
    echo "  3. ./sema-join.sh ai setup"
    echo "  4. ./sema-join.sh ai serve"
    echo "  5. ./sema-join.sh run"
    echo ""
}


# Main script logic
main() {
    # If no arguments, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # Parse command line arguments
    case "$1" in
        install)
            case "$2" in
                backend) install_backend ;;
                frontend) install_frontend ;;
                all) install_all ;;
                *) log_error "Unknown install target: $2"; show_help; exit 1 ;;
            esac
            ;;
        run)
            case "$2" in
                "") run_both ;;  # No argument means run both
                backend) run_backend ;;
                frontend) run_frontend ;;
                *) log_error "Unknown run target: $2"; show_help; exit 1 ;;
            esac
            ;;
        db)
            setup_database
            ;;
        tests|test)
            run_tests
            ;;
        status)
            show_status
            ;;
        ai)
            case "$2" in
                setup) ai_setup ;;
                status) ai_status ;;
                serve) ai_serve ;;
                "") log_error "AI command requires an argument"; echo ""; echo "Available: setup, status, serve"; exit 1 ;;
                *) log_error "Unknown ai command: $2"; echo ""; echo "Available: setup, status, serve"; exit 1 ;;
            esac
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

