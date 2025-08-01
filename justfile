# Justfile for daytraid project

# Default recipe
default:
    @just --list

# Kill process running on specified port
kill-port port:
    @echo "Killing process on port {{port}}..."
    @lsof -ti:{{port}} | xargs kill -9 2>/dev/null || echo "No process found on port {{port}}"

# Run frontend on port 3000
run-frontend:
    @just kill-port 3000
    @echo "Starting frontend on port 3000..."
    @cd frontend && npm run dev

# Run backend on port 8000
run-backend:
    @just kill-port 8000
    @echo "Starting backend on port 8000..."
    @cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Install frontend dependencies
install-frontend:
    @echo "Installing frontend dependencies..."
    @cd frontend && npm install

# Install backend dependencies
install-backend:
    @echo "Installing backend dependencies..."
    @cd backend && uv sync

# Install all dependencies
install-all:
    @just install-frontend
    @just install-backend

# Run both frontend and backend simultaneously
run-all:
    @echo "Starting both frontend and backend..."
    @just kill-port 3000
    @just kill-port 8000
    @(cd frontend && npm run dev) & (cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload)