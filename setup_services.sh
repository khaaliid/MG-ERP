#!/bin/bash
# Setup script for MG-ERP services

echo "Setting up MG-ERP microservices..."

# Function to setup a service
setup_service() {
    local service_name=$1
    local service_path=$2
    
    echo "Setting up $service_name..."
    cd "$service_path"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment for $service_name..."
        python -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Linux/Mac
        source venv/bin/activate
    fi
    
    echo "Installing dependencies for $service_name..."
    pip install -r requirements.txt
    
    echo "$service_name setup complete!"
    echo ""
}

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Setup each service
setup_service "Ledger" "$SCRIPT_DIR/ledger/backend"
setup_service "POS" "$SCRIPT_DIR/pos/backend" 
setup_service "Inventory" "$SCRIPT_DIR/inventory/backend"

echo "All services setup complete!"
echo ""
echo "To start the services:"
echo "1. Start database: cd db && docker compose up -d"
echo "2. Start Ledger: cd ledger/backend && venv/Scripts/activate && uvicorn app.main:app --reload --port 8000"
echo "3. Start POS: cd pos/backend && venv/Scripts/activate && uvicorn app.main:app --reload --port 8001"
echo "4. Start Inventory: cd inventory/backend && venv/Scripts/activate && uvicorn app.main:app --reload --port 8002"