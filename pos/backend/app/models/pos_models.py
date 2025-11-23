"""
POS Models - Stateless Configuration

This file now contains only configuration and types needed for the stateless POS system.
All data storage is handled by external services (Inventory and Ledger).
"""

# POS is now stateless - no local database models
# All data operations are handled via API calls to:
# - Inventory Service: Product data and stock management  
# - Ledger Service: Financial transactions and accounting

# This file is kept for backward compatibility but contains no models
# Future: Remove this file entirely once all imports are cleaned up