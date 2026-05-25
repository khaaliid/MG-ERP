"""
API Routes for Light Module
Includes Authentication, POS, Inventory, Ledger, and Reports
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime, timedelta
import uuid
import io
import logging
import barcode
from barcode.writer import ImageWriter

# ESC/POS printer support
# Try to import, but gracefully handle if unavailable (e.g., in PyInstaller bundle)
try:
    from escpos.printer import Dummy
    from escpos import printer
    ESCPOS_AVAILABLE = True
except (ImportError, FileNotFoundError, Exception) as e:
    # ESC/POS not available - capabilities.json or other files missing
    ESCPOS_AVAILABLE = False
    import logging
    logging.getLogger(__name__).info(f"ESC/POS thermal printing disabled: {e}")

from database import get_db
from models import LedgerRecord, InventoryItem, POSTransaction, POSItem, TransactionType, PaymentMethod, User, UserRole, Expense, SalesUser, Refund, RefundItem
from schemas import (
    LedgerRecordCreate, LedgerRecordResponse, LedgerPageResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    POSTransactionCreate, POSTransactionResponse, POSTransactionPageResponse,
    SalesReportResponse, InventoryReportResponse, LedgerReportResponse,
    Token, UserLogin, UserCreate, UserUpdate, UserResponse,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    SalesUserCreate, SalesUserUpdate, SalesUserResponse,
    SalesUserPerformanceReportResponse
)
from schemas import POSClosureRequest, POSClosureResponse
from schemas import RefundRequest, RefundResponse
from schemas import ItemRefundRequest, ItemRefundResponse
from schemas import WhatsAppReceiptRequest, WhatsAppReceiptResponse
from config import TAX_RATE
from whatsapp_client import WhatsAppClient
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_cashier, get_current_manager, get_current_super_admin
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_receipt_lines(transaction: POSTransaction, items: List[POSItem]) -> List[str]:
    """Build receipt text lines shared by print and WhatsApp e-receipt."""
    lines: List[str] = []
    lines.append("RECEIPT")
    lines.append("================================")
    lines.append(f"Transaction: {transaction.transaction_number}")
    lines.append(f"Date: {transaction.transaction_date.strftime('%Y-%m-%d %H:%M')}")
    if transaction.customer_name:
        lines.append(f"Customer: {transaction.customer_name}")
    lines.append("================================")

    for item in items:
        item_name = item.product_name or "Unknown Item"
        line_total = item.subtotal if item.subtotal is not None else (item.unit_price * item.quantity)
        lines.append(f"{item_name}")
        lines.append(f"  {item.quantity} x ${item.unit_price:.2f} = ${line_total:.2f}")

    lines.append("================================")
    lines.append(f"Subtotal: ${transaction.subtotal:.2f}")
    if transaction.discount > 0:
        lines.append(f"Discount: -${transaction.discount:.2f}")
    if transaction.tax > 0:
        lines.append(f"Tax: ${transaction.tax:.2f}")
    lines.append(f"TOTAL: ${transaction.total:.2f}")
    payment_method = transaction.payment_method.value if hasattr(transaction.payment_method, 'value') else str(transaction.payment_method)
    lines.append(f"Payment: {payment_method}")
    lines.append("")
    lines.append("Thank you for your business!")
    return lines


# ============= Authentication Routes =============
@router.post("/auth/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/auth/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Create new user (Super Admin only)"""
    # Validate password
    if not user_data.password or len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email exists
    if user_data.email and db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.get("/auth/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """List all users (Manager and Super Admin)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.put("/auth/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Update user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate password if provided
    if user_data.password is not None:
        if not user_data.password or len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
    
    # Update fields
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/auth/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Delete user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting the current user
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()


# ============= Ledger Routes =============
@router.get("/ledger", response_model=Union[List[LedgerRecordResponse], LedgerPageResponse])
def get_ledger_records(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=500),
    transaction_type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    paginated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get all ledger records with optional filtering"""
    query = db.query(LedgerRecord)
    if transaction_type:
        query = query.filter(LedgerRecord.transaction_type == transaction_type)
    if start_date:
        query = query.filter(LedgerRecord.transaction_date >= start_date)
    if end_date:
        query = query.filter(LedgerRecord.transaction_date <= end_date)
    total = query.count()
    records = query.order_by(LedgerRecord.transaction_date.desc()).offset(skip).limit(limit).all()
    if paginated:
        return {"items": records, "total": total, "skip": skip, "limit": limit}
    return records


@router.post("/ledger", response_model=LedgerRecordResponse)
def create_ledger_record(
    record: LedgerRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Create a new ledger record"""
    # Get current balance
    last_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    current_balance = last_record.balance if last_record else 0.0
    
    # Calculate new balance
    if record.transaction_type in [TransactionType.SALE]:
        new_balance = current_balance + record.amount
    else:  # PURCHASE, RETURN, ADJUSTMENT
        new_balance = current_balance - record.amount
    
    db_record = LedgerRecord(**record.model_dump(), balance=new_balance)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/ledger/{record_id}", response_model=LedgerRecordResponse)
def get_ledger_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get a specific ledger record"""
    record = db.query(LedgerRecord).filter(LedgerRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Ledger record not found")
    return record


# ============= Inventory Routes =============
@router.get("/inventory", response_model=List[InventoryItemResponse])
def get_inventory_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get all inventory items with optional filtering"""
    query = db.query(InventoryItem)
    if category:
        query = query.filter(InventoryItem.category == category)
    if search:
        query = query.filter(
            (InventoryItem.name.contains(search)) |
            (InventoryItem.sku.contains(search)) |
            (InventoryItem.barcode.contains(search))
        )
    return query.offset(skip).limit(limit).all()


@router.post("/inventory", response_model=InventoryItemResponse)
def create_inventory_item(
    item: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Create a new inventory item"""
    # Check for duplicate SKU
    existing = db.query(InventoryItem).filter(InventoryItem.sku == item.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    db_item = InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/inventory/{item_id}", response_model=InventoryItemResponse)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get a specific inventory item"""
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.put("/inventory/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Update an inventory item"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/inventory/{item_id}")
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Delete an inventory item"""
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted successfully"}


@router.get("/inventory/{item_id}/barcode")
def generate_barcode(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Generate barcode image for an inventory item"""
    import logging
    import sys
    logger = logging.getLogger(__name__)
    
    logger.info(f"Barcode generation requested for item ID: {item_id}")
    
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Use barcode if available, otherwise use SKU
    barcode_value = db_item.barcode if db_item.barcode else db_item.sku
    logger.info(f"Item {item_id}: name={db_item.name}, sku={db_item.sku}, barcode={db_item.barcode}, using value={barcode_value}")
    
    if not barcode_value:
        logger.error(f"Item {item_id} has no barcode or SKU")
        raise HTTPException(status_code=400, detail="No barcode or SKU available for this item")
    
    # Generate barcode (EAN13 format if 12-13 digits, otherwise Code128)
    try:
        # Clean the barcode value
        barcode_value_clean = str(barcode_value).strip()
        logger.info(f"Cleaned barcode value: '{barcode_value_clean}' (length: {len(barcode_value_clean)}, isdigit: {barcode_value_clean.isdigit()})")
        
        if barcode_value_clean.isdigit():
            if len(barcode_value_clean) == 12:
                # EAN13 requires 12 digits (13th is checksum)
                barcode_class = barcode.get_barcode_class('ean13')
                logger.info("Using EAN13 format (12 digits)")
            elif len(barcode_value_clean) == 13:
                # Already has checksum, use first 12 digits
                barcode_value_clean = barcode_value_clean[:12]
                barcode_class = barcode.get_barcode_class('ean13')
                logger.info("Using EAN13 format (13 digits, truncated to 12)")
            else:
                # Use Code128 for other numeric formats
                barcode_class = barcode.get_barcode_class('code128')
                logger.info(f"Using Code128 format (numeric, {len(barcode_value_clean)} digits)")
        else:
            # Code128 works with any alphanumeric
            barcode_class = barcode.get_barcode_class('code128')
            logger.info("Using Code128 format (alphanumeric)")
        
        # Create barcode with image writer
        barcode_instance = barcode_class(barcode_value_clean, writer=ImageWriter())
        
        # Generate to buffer
        buffer = io.BytesIO()
        
        barcode_instance.write(buffer, options={
            'module_width': 0.3,
            'module_height': 10.0,
            'font_size': 10,
            'text_distance': 5,
            'quiet_zone': 6.5,
            'write_text': True,
        })
        
        buffer.seek(0)
        
        logger.info(f"Barcode generated successfully for item {item_id}")
        return StreamingResponse(buffer, media_type="image/png")
    
    except Exception as e:
        # Return more detailed error information
        logger.error(f"Barcode generation failed for item {item_id}, value '{barcode_value}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to generate barcode for value '{barcode_value}': {str(e)}"
        )


@router.get("/inventory/{item_id}/barcode/escpos")
def generate_barcode_escpos(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Generate ESC/POS commands for printing barcode on thermal printer"""
    
    if not ESCPOS_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="ESC/POS library not installed. Run: pip install python-escpos"
        )
    
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Use barcode if available, otherwise use SKU
    barcode_value = db_item.barcode if db_item.barcode else db_item.sku
    
    try:
        # Create a dummy printer to generate ESC/POS commands
        d = Dummy()
        
        # Set up the printer - use bold() method instead of text_type parameter
        d.set(align='center', double_width=True, double_height=True)
        d.text(f"{db_item.name}\n")
        d.set(align='center', double_width=False, double_height=False)
        d.text(f"Price: ${db_item.unit_price:.2f}\n\n")
        
        # Print barcode (EAN13 or CODE128)
        barcode_clean = str(barcode_value).strip()
        if barcode_clean.isdigit() and len(barcode_clean) in [12, 13]:
            # Use EAN13 for 12-13 digit codes
            if len(barcode_clean) == 13:
                barcode_clean = barcode_clean[:12]  # Remove checksum
            d.barcode(barcode_clean, 'EAN13', height=80, width=3, pos='BELOW')
        else:
            # Use CODE128 for other formats
            d.barcode(barcode_clean, 'CODE128', height=80, width=3, pos='BELOW')
        
        d.text("\n")
        d.cut()
        
        # Get the raw ESC/POS commands
        escpos_data = bytes(d.output)
        
        return Response(content=escpos_data, media_type="application/octet-stream")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ESC/POS barcode: {str(e)}"
        )


def calculate_ean13_checksum(barcode_12: str) -> int:
    """Calculate EAN13 checksum digit"""
    odd_sum = sum(int(barcode_12[i]) for i in range(0, 12, 2))
    even_sum = sum(int(barcode_12[i]) for i in range(1, 12, 2))
    total = odd_sum + (even_sum * 3)
    checksum = (10 - (total % 10)) % 10
    return checksum


# ============= POS Routes =============
@router.get("/pos/transactions", response_model=Union[List[POSTransactionResponse], POSTransactionPageResponse])
def get_pos_transactions(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=500),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    payment_method: Optional[str] = None,
    paginated: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get all POS transactions with optional date/search filtering"""
    query = db.query(POSTransaction)
    if start_date:
        query = query.filter(POSTransaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(POSTransaction.transaction_date <= end_date)

    search_term = (search or '').strip()
    if search_term:
        filters = [POSTransaction.transaction_number.ilike(f"%{search_term}%")]
        if search_term.isdigit():
            filters.append(POSTransaction.id == int(search_term))
        query = query.filter(or_(*filters))

    payment_method_term = (payment_method or '').strip().lower()
    if payment_method_term and payment_method_term != 'all':
        try:
            parsed_payment_method = PaymentMethod(payment_method_term)
            query = query.filter(POSTransaction.payment_method == parsed_payment_method)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payment method filter")

    total = query.count()
    transactions = query.order_by(POSTransaction.transaction_date.desc()).offset(skip).limit(limit).all()

    if paginated:
        return {
            "items": transactions,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    return transactions


@router.post("/pos/transactions", response_model=POSTransactionResponse)
def create_pos_transaction(
    transaction: POSTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Create a new POS transaction"""
    logger.info(
        "POS create start | user_id=%s | sales_user_id=%s | items_count=%s | payment_method=%s | payment_received=%s | discount=%s",
        getattr(current_user, "id", None),
        transaction.sales_user_id,
        len(transaction.items or []),
        transaction.payment_method,
        transaction.payment_received,
        transaction.discount,
    )

    # Generate transaction number
    trans_number = f"POS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    logger.info("POS transaction_number generated | transaction_number=%s", trans_number)
    
    # Calculate totals
    subtotal = 0.0
    pos_items = []
    
    for item in transaction.items:
        logger.debug("POS item validating | inventory_id=%s | quantity=%s", item.inventory_id, item.quantity)
        # Get inventory item
        inv_item = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_id).first()
        if not inv_item:
            logger.warning("POS item not found | transaction_number=%s | inventory_id=%s", trans_number, item.inventory_id)
            raise HTTPException(status_code=404, detail=f"Inventory item {item.inventory_id} not found")
        
        # Check stock
        if inv_item.quantity < item.quantity:
            logger.warning(
                "POS insufficient stock | transaction_number=%s | inventory_id=%s | requested=%s | available=%s",
                trans_number,
                item.inventory_id,
                item.quantity,
                inv_item.quantity,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {inv_item.name}. Available: {inv_item.quantity}"
            )
        
        # Calculate item subtotal
        item_subtotal = inv_item.unit_price * item.quantity
        subtotal += item_subtotal
        
        # Create POS item
        pos_items.append({
            "inventory_id": item.inventory_id,
            "product_name": inv_item.name,
            "quantity": item.quantity,
            "unit_price": inv_item.unit_price,
            "subtotal": item_subtotal
        })
        
        # Update inventory
        inv_item.quantity -= item.quantity
    
    # Calculate tax and total
    tax = subtotal * TAX_RATE
    total = subtotal + tax - transaction.discount
    logger.info(
        "POS totals calculated | transaction_number=%s | subtotal=%.2f | tax=%.2f | discount=%.2f | total=%.2f",
        trans_number,
        subtotal,
        tax,
        transaction.discount,
        total,
    )
    
    # Calculate change
    change = transaction.payment_received - total
    if change < 0:
        logger.warning(
            "POS insufficient payment | transaction_number=%s | payment_received=%.2f | required_total=%.2f",
            trans_number,
            transaction.payment_received,
            total,
        )
        raise HTTPException(status_code=400, detail="Insufficient payment received")
    
    # Create POS transaction
    db_transaction = POSTransaction(
        transaction_number=trans_number,
        customer_name=transaction.customer_name,
        subtotal=subtotal,
        tax=tax,
        discount=transaction.discount,
        total=total,
        payment_method=transaction.payment_method,
        payment_received=transaction.payment_received,
        change_returned=change,
        sales_user_id=transaction.sales_user_id,
        notes=transaction.notes
    )
    db.add(db_transaction)
    db.flush()
    logger.info("POS transaction persisted | transaction_number=%s | transaction_id=%s", trans_number, db_transaction.id)
    
    # Add POS items
    for item_data in pos_items:
        pos_item = POSItem(transaction_id=db_transaction.id, **item_data)
        db.add(pos_item)
    
    # Create ledger record
    ledger_record = LedgerRecord(
        transaction_type=TransactionType.SALE,
        description=f"POS Sale - {trans_number}",
        amount=total,
        balance=0.0,  # Will be calculated
        reference_id=trans_number,
        payment_method=transaction.payment_method,
        notes=transaction.notes
    )
    
    # Calculate balance
    last_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    ledger_record.balance = (last_record.balance if last_record else 0.0) + total
    
    db.add(ledger_record)
    db.flush()
    logger.info(
        "POS ledger record persisted | transaction_number=%s | ledger_id=%s | balance=%.2f",
        trans_number,
        ledger_record.id,
        ledger_record.balance,
    )
    
    db_transaction.ledger_id = ledger_record.id
    
    db.commit()
    logger.info("POS create committed | transaction_number=%s | transaction_id=%s", trans_number, db_transaction.id)
    db.refresh(db_transaction)
    return db_transaction


@router.get("/pos/transactions/{transaction_id}", response_model=POSTransactionResponse)
def get_pos_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get a specific POS transaction"""
    transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.get("/pos/transactions/{transaction_id}/receipt/escpos")
def generate_receipt_escpos(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Generate ESC/POS receipt for a POS transaction"""
    
    if not ESCPOS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ESC/POS library not available. Please install: pip install python-escpos"
        )
    
    transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    try:
        items = db.query(POSItem).filter(POSItem.transaction_id == transaction_id).all()
        receipt_lines = _build_receipt_lines(transaction, items)

        # Create a dummy printer to generate ESC/POS commands
        d = Dummy()

        d.set(align='left', double_width=False, double_height=False)
        for idx, line in enumerate(receipt_lines):
            if line.startswith("RECEIPT"):
                d.set(align='center', double_width=True, double_height=True)
                d.text(f"{line}\n")
                d.set(align='left', double_width=False, double_height=False)
            elif line.startswith("TOTAL:"):
                d.set(double_width=True, double_height=True)
                d.text(f"{line}\n")
                d.set(double_width=False, double_height=False)
            elif idx == len(receipt_lines) - 1:
                d.set(align='center')
                d.text(f"{line}\n")
                d.set(align='left')
            else:
                d.text(f"{line}\n")

        d.text("\n")
        
        # Cut paper
        d.cut()
        
        # Get the raw ESC/POS commands
        escpos_data = bytes(d.output)
        
        return Response(content=escpos_data, media_type="application/octet-stream")
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate ESC/POS receipt: {str(e)}"
        )
    raise HTTPException(
        status_code=501,
        detail="ESC/POS thermal printer receipt generation is not available in portable version."
    )
    
    # Note: Original thermal printer code removed for portable compatibility


@router.post("/pos/transactions/{transaction_id}/receipt/whatsapp", response_model=WhatsAppReceiptResponse)
def send_receipt_whatsapp(
    transaction_id: int,
    req: WhatsAppReceiptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Send e-receipt for a transaction through WhatsApp."""
    logger.info(
        "WhatsApp receipt send start | transaction_id=%s | user_id=%s",
        transaction_id,
        getattr(current_user, "id", None),
    )

    transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
    if not transaction:
        logger.warning("WhatsApp receipt transaction not found | transaction_id=%s", transaction_id)
        raise HTTPException(status_code=404, detail="Transaction not found")

    phone_number = (req.phone_number or "").strip()
    if not phone_number:
        logger.warning("WhatsApp receipt missing phone_number | transaction_id=%s", transaction_id)
        raise HTTPException(status_code=400, detail="phone_number is required")

    items = db.query(POSItem).filter(POSItem.transaction_id == transaction_id).all()
    receipt_text = "\n".join(_build_receipt_lines(transaction, items))
    logger.info(
        "WhatsApp receipt payload ready | transaction_id=%s | phone_number=%s | items_count=%s | message_chars=%s",
        transaction_id,
        phone_number,
        len(items),
        len(receipt_text),
    )

    try:
        wa_client = WhatsAppClient()
        provider_response = wa_client.send_text_message(phone_number, receipt_text)
        logger.info(
            "WhatsApp receipt send success | transaction_id=%s | phone_number=%s | provider_keys=%s",
            transaction_id,
            phone_number,
            list(provider_response.keys()) if isinstance(provider_response, dict) else type(provider_response),
        )
    except ValueError as exc:
        logger.exception(
            "WhatsApp receipt validation/config error | transaction_id=%s | phone_number=%s",
            transaction_id,
            phone_number,
        )
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception(
            "WhatsApp receipt send failed | transaction_id=%s | phone_number=%s",
            transaction_id,
            phone_number,
        )
        raise HTTPException(status_code=502, detail=f"Failed to send WhatsApp receipt: {str(exc)}")

    return WhatsAppReceiptResponse(
        transaction_id=transaction_id,
        phone_number=phone_number,
        message="E-receipt sent successfully",
        provider_response=provider_response,
    )


# ============= POS Cashier Closure =============
@router.post("/pos/closures", response_model=POSClosureResponse)
def create_pos_closure(
    closure: POSClosureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Create a cashier closure summary and optionally save it to the ledger

    - Computes transactions for the given sales_user_id in the date range
    - Returns summary and list of transactions
    - If `save_to_ledger` is true, writes a single ledger record with the total
    """
    # normalize dates
    start_date = closure.start_date or (datetime.utcnow() - timedelta(days=1))
    end_date = closure.end_date or datetime.utcnow()

    txns_query = db.query(POSTransaction).filter(
        POSTransaction.transaction_date >= start_date,
        POSTransaction.transaction_date <= end_date,
        POSTransaction.sales_user_id == closure.sales_user_id
    )
    transactions = txns_query.order_by(POSTransaction.transaction_date.desc()).all()

    total_sales = sum(t.total for t in transactions)
    transaction_count = len(transactions)
    by_method = {}
    for t in transactions:
        m = (t.payment_method.value if hasattr(t.payment_method, 'value') else str(t.payment_method)) or 'cash'
        by_method[m] = by_method.get(m, 0.0) + (t.payment_received or t.total or 0.0)

    # Optionally persist a ledger record
    if closure.save_to_ledger:
        ledger_record = LedgerRecord(
            transaction_type=TransactionType.SALE,
            description=f"Cashier closure - sales_user:{closure.sales_user_id}",
            amount=total_sales,
            balance=0.0,
            reference_id=f"closure-{closure.sales_user_id}-{datetime.utcnow().isoformat()}",
            payment_method=None,
            notes=f"Transactions: {transaction_count}"
        )
        # compute balance based on last ledger record
        last_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
        ledger_record.balance = (last_record.balance if last_record else 0.0) + total_sales
        db.add(ledger_record)
        db.commit()

    # prepare response transactions (convert to response schema compatible dicts)
    resp_txns = []
    for t in transactions:
        resp_txns.append(t)

    return POSClosureResponse(
        sales_user_id=closure.sales_user_id,
        start_date=start_date,
        end_date=end_date,
        total_sales=total_sales,
        transaction_count=transaction_count,
        by_payment_method=by_method,
        transactions=resp_txns
    )


# ============= POS Refund =============
@router.post("/pos/transactions/{transaction_id}/refund", response_model=RefundResponse)
def refund_pos_transaction(
    transaction_id: int,
    refund: RefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Process a refund for a POS transaction (minimal):

    - Validates refund amount <= original transaction total
    - Optionally restocks inventory items
    - Creates a LedgerRecord with TransactionType.RETURN and deducts from balance
    """
    # find transaction
    transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    existing_refund = db.query(Refund).filter(Refund.transaction_id == transaction_id).first()
    if existing_refund:
        raise HTTPException(status_code=409, detail="Transaction has already been refunded")

    existing_refund_ledger = db.query(LedgerRecord).filter(
        LedgerRecord.transaction_type == TransactionType.RETURN,
        LedgerRecord.reference_id == transaction.transaction_number
    ).first()
    if existing_refund_ledger:
        raise HTTPException(status_code=409, detail="Transaction has already been refunded")

    if refund.amount <= 0 or refund.amount > (transaction.total or 0.0):
        raise HTTPException(status_code=400, detail="Invalid refund amount")

    # Restock inventory if requested
    restocked = False
    if refund.restock:
        items = db.query(POSItem).filter(POSItem.transaction_id == transaction_id).all()
        for item in items:
            inv = db.query(InventoryItem).filter(InventoryItem.id == item.inventory_id).first()
            if inv:
                inv.quantity = (inv.quantity or 0) + (item.quantity or 0)
        restocked = True

    # Create ledger record for the refund (treat as RETURN)
    ledger_record = LedgerRecord(
        transaction_type=TransactionType.RETURN,
        description=f"Refund - {transaction.transaction_number}",
        amount=refund.amount,
        balance=0.0,
        reference_id=transaction.transaction_number,
        payment_method=(refund.refund_payment_method or transaction.payment_method),
        notes=refund.reason or None
    )

    last_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    ledger_record.balance = (last_record.balance if last_record else 0.0) - refund.amount

    db.add(ledger_record)
    db.flush()

    # Persist Refund record
    refund_record = Refund(
        transaction_id=transaction_id,
        amount=refund.amount,
        refund_date=ledger_record.transaction_date,
        reason=refund.reason,
        restocked=restocked,
        processed_by=(current_user.id if current_user is not None else None),
        ledger_id=ledger_record.id
    )
    db.add(refund_record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Transaction has already been refunded")

    return RefundResponse(
        transaction_id=transaction_id,
        refunded_amount=refund.amount,
        refund_date=ledger_record.transaction_date,
        new_balance=ledger_record.balance,
        restocked=restocked,
        notes=ledger_record.notes
    )


@router.post("/pos/transactions/{transaction_id}/refund-item", response_model=ItemRefundResponse)
def refund_pos_transaction_item(
    transaction_id: int,
    refund: ItemRefundRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Refund a specific item (and quantity) from a POS transaction."""
    transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    pos_item = db.query(POSItem).filter(
        POSItem.id == refund.pos_item_id,
        POSItem.transaction_id == transaction_id
    ).first()
    if not pos_item:
        raise HTTPException(status_code=404, detail="Transaction item not found")

    existing_item_refund = db.query(RefundItem).filter(
        RefundItem.transaction_id == transaction_id,
        RefundItem.pos_item_id == refund.pos_item_id
    ).first()
    if existing_item_refund:
        raise HTTPException(status_code=409, detail="This item has already been refunded")

    refunded_qty = db.query(func.coalesce(func.sum(RefundItem.refunded_quantity), 0)).filter(
        RefundItem.transaction_id == transaction_id,
        RefundItem.pos_item_id == refund.pos_item_id
    ).scalar() or 0

    refunded_amount = db.query(func.coalesce(func.sum(RefundItem.refunded_amount), 0.0)).filter(
        RefundItem.transaction_id == transaction_id,
        RefundItem.pos_item_id == refund.pos_item_id
    ).scalar() or 0.0

    remaining_qty = (pos_item.quantity or 0) - int(refunded_qty)
    if remaining_qty <= 0:
        raise HTTPException(status_code=409, detail="This item has already been fully refunded")

    if refund.quantity > remaining_qty:
        raise HTTPException(
            status_code=400,
            detail=f"Refund quantity exceeds remaining quantity ({remaining_qty})"
        )

    # Apply the transaction-level effective ratio so item refunds reflect tax/discount impacts.
    base_subtotal = transaction.subtotal or 0.0
    effective_ratio = (transaction.total / base_subtotal) if base_subtotal > 0 else 1.0
    line_refund_base = (pos_item.unit_price or 0.0) * refund.quantity
    line_refund_amount = round(line_refund_base * effective_ratio, 2)

    max_item_amount = round((pos_item.subtotal or 0.0) * effective_ratio, 2)
    remaining_item_amount = round(max_item_amount - refunded_amount, 2)
    if remaining_item_amount <= 0:
        raise HTTPException(status_code=409, detail="This item has no refundable amount remaining")

    if refund.quantity == remaining_qty:
        line_refund_amount = remaining_item_amount
    else:
        line_refund_amount = min(line_refund_amount, remaining_item_amount)

    if line_refund_amount <= 0:
        raise HTTPException(status_code=400, detail="Calculated refund amount is invalid")

    if refund.restock:
        inv = db.query(InventoryItem).filter(InventoryItem.id == pos_item.inventory_id).first()
        if inv:
            inv.quantity = (inv.quantity or 0) + refund.quantity

    ledger_record = LedgerRecord(
        transaction_type=TransactionType.RETURN,
        description=f"Item refund - {transaction.transaction_number} - {pos_item.product_name}",
        amount=line_refund_amount,
        balance=0.0,
        reference_id=transaction.transaction_number,
        payment_method=(refund.refund_payment_method or transaction.payment_method),
        notes=refund.reason or None
    )

    last_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    ledger_record.balance = (last_record.balance if last_record else 0.0) - line_refund_amount

    db.add(ledger_record)
    db.flush()

    refund_record = Refund(
        transaction_id=transaction_id,
        amount=line_refund_amount,
        refund_date=ledger_record.transaction_date,
        reason=refund.reason,
        restocked=bool(refund.restock),
        processed_by=(current_user.id if current_user is not None else None),
        ledger_id=ledger_record.id
    )
    db.add(refund_record)
    db.flush()

    refund_item = RefundItem(
        refund_id=refund_record.id,
        transaction_id=transaction_id,
        pos_item_id=pos_item.id,
        inventory_id=pos_item.inventory_id,
        refunded_quantity=refund.quantity,
        refunded_amount=line_refund_amount,
    )
    db.add(refund_item)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Failed to process item refund")

    return ItemRefundResponse(
        transaction_id=transaction_id,
        pos_item_id=pos_item.id,
        refunded_quantity=refund.quantity,
        refunded_amount=line_refund_amount,
        refund_date=ledger_record.transaction_date,
        new_balance=ledger_record.balance,
        restocked=bool(refund.restock),
        remaining_quantity=remaining_qty - refund.quantity,
        notes=ledger_record.notes,
    )


# ============= Reports Routes =============
@router.get("/reports/sales", response_model=SalesReportResponse)
def get_sales_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get sales report for a date range"""
    query = db.query(POSTransaction)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = query.filter(
        POSTransaction.transaction_date >= start_date,
        POSTransaction.transaction_date <= end_date
    )
    
    transactions = query.all()
    
    total_sales = sum(t.total for t in transactions)
    total_tax = sum(t.tax for t in transactions)
    total_discount = sum(t.discount for t in transactions)
    transaction_count = len(transactions)
    avg_transaction = total_sales / transaction_count if transaction_count > 0 else 0.0
    
    return SalesReportResponse(
        total_sales=total_sales,
        total_transactions=transaction_count,
        average_transaction=avg_transaction,
        total_tax=total_tax,
        total_discount=total_discount
    )


@router.get("/reports/inventory", response_model=InventoryReportResponse)
def get_inventory_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get inventory status report"""
    items = db.query(InventoryItem).all()
    
    total_items = len(items)
    total_value = sum(item.quantity * item.unit_price for item in items)
    low_stock = sum(1 for item in items if 0 < item.quantity <= item.reorder_level)
    out_of_stock = sum(1 for item in items if item.quantity == 0)
    
    return InventoryReportResponse(
        total_items=total_items,
        total_value=total_value,
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock
    )


@router.get("/reports/ledger", response_model=LedgerReportResponse)
def get_ledger_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get ledger summary report"""
    query = db.query(LedgerRecord)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    query = query.filter(
        LedgerRecord.transaction_date >= start_date,
        LedgerRecord.transaction_date <= end_date
    )
    
    records = query.all()
    
    # Get current balance (from latest record overall)
    latest_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    current_balance = latest_record.balance if latest_record else 0.0
    
    # Calculate income and expenses
    income = sum(r.amount for r in records if r.transaction_type == TransactionType.SALE)
    expenses = sum(r.amount for r in records if r.transaction_type in [TransactionType.PURCHASE, TransactionType.ADJUSTMENT])
    
    return LedgerReportResponse(
        current_balance=current_balance,
        total_income=income,
        total_expenses=expenses,
        transaction_count=len(records)
    )


@router.get("/reports/sales-users", response_model=SalesUserPerformanceReportResponse)
def get_sales_user_performance_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get sales user performance report showing pieces sold and revenue per user"""
    if not start_date:
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Get all sales users (including inactive to show historical data)
    sales_users = db.query(SalesUser).all()
    
    performance_list = []
    total_transactions_overall = 0
    total_pieces_overall = 0
    total_revenue_overall = 0.0
    
    # Process each sales user
    for user in sales_users:
        # Get transactions for this sales user in date range
        transactions = db.query(POSTransaction).filter(
            POSTransaction.sales_user_id == user.id,
            POSTransaction.transaction_date >= start_date,
            POSTransaction.transaction_date <= end_date
        ).all()
        
        if not transactions:
            continue  # Skip users with no transactions
        
        transaction_count = len(transactions)
        total_revenue = sum(t.total for t in transactions)
        
        # Get product breakdown
        product_breakdown = {}
        for transaction in transactions:
            items = db.query(POSItem).filter(POSItem.transaction_id == transaction.id).all()
            for item in items:
                if item.product_name not in product_breakdown:
                    product_breakdown[item.product_name] = {
                        'quantity': 0,
                        'total_amount': 0.0
                    }
                product_breakdown[item.product_name]['quantity'] += item.quantity
                product_breakdown[item.product_name]['total_amount'] += item.subtotal
        
        # Convert breakdown to list
        breakdown_list = [
            {
                'product_name': name,
                'quantity': data['quantity'],
                'total_amount': data['total_amount']
            }
            for name, data in product_breakdown.items()
        ]
        
        # Sort by quantity descending
        breakdown_list.sort(key=lambda x: x['quantity'], reverse=True)
        
        total_pieces = sum(item['quantity'] for item in breakdown_list)
        
        performance_list.append({
            'sales_user_id': user.id,
            'sales_user_name': user.name,
            'employee_code': user.employee_code,
            'total_transactions': transaction_count,
            'total_pieces': total_pieces,
            'total_revenue': total_revenue,
            'product_breakdown': breakdown_list
        })
        
        total_transactions_overall += transaction_count
        total_pieces_overall += total_pieces
        total_revenue_overall += total_revenue
    
    # Handle transactions without sales_user_id (legacy data)
    unassigned_transactions = db.query(POSTransaction).filter(
        POSTransaction.sales_user_id == None,
        POSTransaction.transaction_date >= start_date,
        POSTransaction.transaction_date <= end_date
    ).all()
    
    if unassigned_transactions:
        transaction_count = len(unassigned_transactions)
        total_revenue = sum(t.total for t in unassigned_transactions)
        
        # Get product breakdown
        product_breakdown = {}
        for transaction in unassigned_transactions:
            items = db.query(POSItem).filter(POSItem.transaction_id == transaction.id).all()
            for item in items:
                if item.product_name not in product_breakdown:
                    product_breakdown[item.product_name] = {
                        'quantity': 0,
                        'total_amount': 0.0
                    }
                product_breakdown[item.product_name]['quantity'] += item.quantity
                product_breakdown[item.product_name]['total_amount'] += item.subtotal
        
        breakdown_list = [
            {
                'product_name': name,
                'quantity': data['quantity'],
                'total_amount': data['total_amount']
            }
            for name, data in product_breakdown.items()
        ]
        breakdown_list.sort(key=lambda x: x['quantity'], reverse=True)
        
        total_pieces = sum(item['quantity'] for item in breakdown_list)
        
        performance_list.append({
            'sales_user_id': 0,
            'sales_user_name': 'Unassigned',
            'employee_code': None,
            'total_transactions': transaction_count,
            'total_pieces': total_pieces,
            'total_revenue': total_revenue,
            'product_breakdown': breakdown_list
        })
        
        total_transactions_overall += transaction_count
        total_pieces_overall += total_pieces
        total_revenue_overall += total_revenue
    
    # Sort by revenue descending
    performance_list.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    return SalesUserPerformanceReportResponse(
        report_date=datetime.utcnow(),
        start_date=start_date,
        end_date=end_date,
        sales_users=performance_list,
        total_transactions=total_transactions_overall,
        total_pieces=total_pieces_overall,
        total_revenue=total_revenue_overall
    )


# ============= Expense Routes =============
@router.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get all expenses with optional filtering"""
    query = db.query(Expense)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if category:
        query = query.filter(Expense.category == category)
    
    return query.order_by(Expense.expense_date.desc()).all()


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Get a specific expense by ID"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Create a new expense and record in ledger"""
    # Create expense record
    new_expense = Expense(
        **expense.model_dump(),
        recorded_by=current_user.id
    )
    db.add(new_expense)
    db.flush()
    
    # Get latest balance
    latest_record = db.query(LedgerRecord).order_by(LedgerRecord.id.desc()).first()
    current_balance = latest_record.balance if latest_record else 0.0
    
    # Create ledger entry for expense (reduces balance)
    ledger_entry = LedgerRecord(
        transaction_date=expense.expense_date,
        transaction_type=TransactionType.PURCHASE,
        description=f"Expense: {expense.description}",
        amount=expense.amount,
        balance=current_balance - expense.amount,
        reference_id=f"EXP-{new_expense.id}",
        payment_method=expense.payment_method,
        notes=f"Category: {expense.category}"
    )
    db.add(ledger_entry)
    db.flush()
    
    # Update expense with ledger ID
    new_expense.ledger_id = ledger_entry.id
    db.commit()
    db.refresh(new_expense)
    
    return new_expense


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Update an existing expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Update expense fields
    update_data = expense_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Delete an expense (super admin only)"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============= Sales User Routes =============
@router.get("/sales-users", response_model=List[SalesUserResponse])
def get_sales_users(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get all sales users"""
    query = db.query(SalesUser)
    if active_only:
        query = query.filter(SalesUser.is_active == True)
    return query.order_by(SalesUser.name).all()


@router.get("/sales-users/{user_id}", response_model=SalesUserResponse)
def get_sales_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_cashier)
):
    """Get a specific sales user by ID"""
    sales_user = db.query(SalesUser).filter(SalesUser.id == user_id).first()
    if not sales_user:
        raise HTTPException(status_code=404, detail="Sales user not found")
    return sales_user


@router.post("/sales-users", response_model=SalesUserResponse, status_code=status.HTTP_201_CREATED)
def create_sales_user(
    sales_user: SalesUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Create a new sales user"""
    # Check for duplicate employee code
    if sales_user.employee_code:
        existing = db.query(SalesUser).filter(
            SalesUser.employee_code == sales_user.employee_code
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Employee code already exists"
            )
    
    new_user = SalesUser(**sales_user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/sales-users/{user_id}", response_model=SalesUserResponse)
def update_sales_user(
    user_id: int,
    user_update: SalesUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """Update an existing sales user"""
    sales_user = db.query(SalesUser).filter(SalesUser.id == user_id).first()
    if not sales_user:
        raise HTTPException(status_code=404, detail="Sales user not found")
    
    # Check for duplicate employee code if being updated
    update_data = user_update.model_dump(exclude_unset=True)
    if 'employee_code' in update_data and update_data['employee_code']:
        existing = db.query(SalesUser).filter(
            SalesUser.employee_code == update_data['employee_code'],
            SalesUser.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Employee code already exists"
            )
    
    for key, value in update_data.items():
        setattr(sales_user, key, value)
    
    db.commit()
    db.refresh(sales_user)
    return sales_user


@router.delete("/sales-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Delete a sales user (super admin only)"""
    sales_user = db.query(SalesUser).filter(SalesUser.id == user_id).first()
    if not sales_user:
        raise HTTPException(status_code=404, detail="Sales user not found")
    
    db.delete(sales_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Health check
@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "light-module"}
