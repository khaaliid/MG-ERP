# POS Local Database Implementation

## Overview

Converted POS from stateless to persistent architecture with:
- **Local PostgreSQL storage** for sales and items
- **Async broker queue** for ledger synchronization
- **Resilient design** supporting offline operation

## Architecture Changes

### Before (Stateless)
```
POS → Inventory Service (stock check)
    → Ledger Service (immediate sync, blocking)
```

### After (Local DB + Broker)
```
POS → Local PostgreSQL (save sale + items)
    → Inventory Service (immediate stock update)
    → Broker Queue → Background Worker → Ledger Service (async retry)
```

## Implementation Details

### 1. Database Schema (`pos` schema in shared PostgreSQL)

**Sales Table:**
- `id` (PK), `sale_number` (unique)
- Amounts: `subtotal`, `tax_amount`, `discount_amount`, `total_amount`
- Payment: `payment_method`, `tendered_amount`, `change_amount`
- Metadata: `customer_name`, `notes`, `cashier`, `cashier_id`
- Timestamps: `created_at`
- Sync: `status` (pending/synced/failed), `ledger_entry_id`

**Sale Items Table:**
- `id` (PK, auto-increment)
- `sale_id` (FK → sales.id)
- Product: `product_id`, `sku`, `name`
- Pricing: `quantity`, `unit_price`, `discount`, `tax`, `line_total`

### 2. Core Components

**Files Created/Modified:**

- `localdb.py` - SQLAlchemy models (Sale, SaleItem) with `pos` schema
- `config.py` - Async PostgreSQL engine setup (asyncpg)
- `sales_repository.py` - Async CRUD for sales with pagination
- `broker.py` - In-process queue with background worker thread
- `ledger_sync_worker.py` - Handler for async ledger sync with retries
- `routes/local_sales.py` - Fast local endpoints for POS UI
- `services/pos_service.py` - Updated to persist locally + publish
- `main.py` - Startup: create schema/tables, start broker worker

### 3. Sale Processing Flow

```python
# 1. Validate products (Inventory Service)
for item in sale_items:
    product = await inventory_service.get_product_by_id(...)
    # Check stock availability

# 2. Save locally (PostgreSQL)
sale = await repo.save_sale({
    'sale_number': 'POS-20251214-ABC123',
    'items': validated_items,
    'status': 'pending',
    ...
})

# 3. Update inventory (immediate)
await inventory_service.update_stock(product_id, -quantity)

# 4. Publish to broker (async ledger sync)
broker.publish_sale({
    'sale_number': sale_number,
    'items': items,
    'totals': {...},
    'auth_token': token
})

# 5. Return to POS (instant)
return {'sale_number': ..., 'status': 'pending', 'sync_status': 'queued'}
```

### 4. Background Sync Worker

```python
# Worker processes broker queue
async def handle_sale_message(msg):
    # Extract sale_number from message
    # Call ledger service API
    ledger_response = await erp_service.create_sale_entry(...)
    
    # Update local DB status
    if success:
        await repo.update_sale_status(sale_number, 'synced', ledger_entry_id)
    else:
        await repo.update_sale_status(sale_number, 'failed')
        raise  # Broker will retry
```

### 5. New Endpoints

**Local Sales (Fast, No Ledger Dependency):**

- `GET /api/v1/pos/local/sales` - List local sales with items
  - Pagination: `?page=1&limit=50`
  - Filters: `?start_date=2025-12-13&end_date=2025-12-14`
  - Returns: Sales with sync status, ledger references

- `GET /api/v1/pos/local/sales/{sale_number}` - Get single sale
  - Returns: Full sale details with line items
  - Instant response from local DB

**Existing Sales Endpoints:**
- `POST /api/v1/sales/` - Create sale (now saves locally + queues)
- `GET /api/v1/sales/` - Still queries ledger for historical reporting

## Benefits

### Business Benefits
1. **Offline Resilience** - Continue sales during network/ledger outages
2. **Fast Checkout** - No waiting for ledger sync
3. **Auditability** - Complete local record of all transactions
4. **Retry Logic** - Failed syncs automatically retry
5. **Data Sovereignty** - Local control of POS data

### Technical Benefits
1. **Async Architecture** - Non-blocking ledger integration
2. **Postgres Schema Isolation** - `pos` schema keeps data organized
3. **Follows Ledger Pattern** - Consistent async/await, SQLAlchemy models
4. **Type Safety** - Pydantic validation + SQLAlchemy types
5. **Scalable** - Broker can be upgraded to Redis/RabbitMQ

## Database Startup

On `docker compose up`, POS backend:
1. Creates `pos` schema if not exists
2. Grants permissions to `mguser`
3. Creates `sales` and `sale_items` tables
4. Starts broker worker thread
5. Registers broker in app state for route access

## Deployment Notes

### Docker Compose (No Changes Needed)
- Uses same `DATABASE_URL` as ledger/inventory
- Connects to shared `postgres:5432` container
- Schema isolation via `pos` prefix

### Environment Variables
```bash
DATABASE_URL=postgresql+asyncpg://mguser:mgpassword@postgres:5432/mgerp
AUTH_SERVICE_URL=http://auth:8004
INVENTORY_SERVICE_URL=http://inventory:8002
LEDGER_SERVICE_URL=http://ledger:8000
```

### Testing

**Verify Schema:**
```sql
-- Connect to PostgreSQL
\c mgerp
\dn  -- List schemas (should see: pos, ledger, inventory, public)
\dt pos.*  -- List pos tables (should see: sales, sale_items)
```

**Test Sale Flow:**
```bash
# 1. Create sale via API
curl -X POST http://localhost:8001/api/v1/sales/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items": [...], "payment_method": "cash"}'

# 2. Check local DB immediately
curl http://localhost:8001/api/v1/pos/local/sales

# 3. Wait ~1s, check sync status
curl http://localhost:8001/api/v1/pos/local/sales/{sale_number}
# Should see: "status": "synced", "ledger_entry_id": "123"
```

## Monitoring

**Check Sync Status:**
```python
# Query local DB for pending/failed sales
SELECT sale_number, status, created_at, ledger_entry_id
FROM pos.sales
WHERE status IN ('pending', 'failed')
ORDER BY created_at DESC;
```

**Broker Queue:**
- Currently in-memory (thread-safe Queue)
- Logs: `[BROKER]` prefix in application logs
- Worker retries automatically on failure

## Future Enhancements

1. **Redis Broker** - Replace in-process queue with Redis for durability
2. **Dead Letter Queue** - Move permanently failed syncs to DLQ
3. **Reconciliation Job** - Periodic check for pending sales > 5 minutes
4. **Metrics** - Prometheus metrics for sync lag, failure rate
5. **Sync API** - Manual trigger endpoint for failed sales
6. **Ledger Webhooks** - Callback confirmation from ledger

## Migration from Stateless

No migration needed - fresh implementation. Old stateless endpoints still work, now enhanced with local storage.

**Behavioral Changes:**
- Sale creation returns immediately (was blocking on ledger)
- Response includes `sync_status: 'queued'` field
- New `/pos/local/sales` endpoints available
- Inventory updates still synchronous (stock accuracy)

## Troubleshooting

**Issue: Sales stuck in 'pending' status**
- Check: Worker logs for exceptions
- Fix: Verify `LEDGER_SERVICE_URL` reachable
- Action: Worker will auto-retry every ~1s

**Issue: Database connection errors**
- Check: `DATABASE_URL` points to postgres:5432
- Verify: `mgerp` database exists, `mguser` has permissions
- Test: `docker exec -it mg-erp-postgres-1 psql -U mguser -d mgerp`

**Issue: Schema not created**
- Check: Application logs for `[DATABASE]` entries
- Verify: FastAPI startup completed without errors
- Manual: `CREATE SCHEMA IF NOT EXISTS pos;`

## Code Quality

- **Async/Await**: All DB operations use async SQLAlchemy
- **Type Hints**: Full typing for repository methods
- **Error Handling**: Try/catch with session rollback
- **Logging**: Structured logging with prefixes
- **Resource Cleanup**: Sessions closed in finally blocks

## Summary

Successfully converted POS from stateless orchestrator to resilient local-first system with async ledger synchronization via broker pattern. Architecture matches ledger/inventory services for consistency while adding offline capability and improved performance.
