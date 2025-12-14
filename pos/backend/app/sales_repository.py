from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, time
from .localdb import Sale, SaleItem

class SalesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_sale(self, sale_data: Dict[str, Any]) -> Sale:
        """Save sale with items to local database."""
        sale = Sale(
            id=sale_data["id"],
            sale_number=sale_data["sale_number"],
            subtotal=sale_data.get("subtotal", 0.0),
            tax_amount=sale_data.get("tax_amount", 0.0),
            discount_amount=sale_data.get("discount_amount", 0.0),
            total_amount=sale_data.get("total_amount", 0.0),
            payment_method=sale_data.get("payment_method"),
            tendered_amount=sale_data.get("tendered_amount"),
            change_amount=sale_data.get("change_amount"),
            customer_name=sale_data.get("customer_name"),
            notes=sale_data.get("notes"),
            cashier=sale_data.get("cashier"),
            cashier_id=sale_data.get("cashier_id"),
            status=sale_data.get("status", "pending"),
            ledger_entry_id=sale_data.get("ledger_entry_id"),
        )
        for item in sale_data.get("items", []):
            sale.items.append(SaleItem(
                product_id=item.get("product_id"),
                sku=item.get("sku"),
                name=item.get("name"),
                quantity=item.get("quantity", 0.0),
                unit_price=item.get("unit_price", 0.0),
                discount=item.get("discount", 0.0),
                tax=item.get("tax", 0.0),
                line_total=item.get("line_total", 0.0),
            ))
        self.session.add(sale)
        await self.session.commit()
        await self.session.refresh(sale, ['items'])
        return sale

    async def get_sale(self, sale_number: str) -> Optional[Sale]:
        """Get sale by sale number with items loaded."""
        stmt = select(Sale).where(Sale.sale_number == sale_number).options(selectinload(Sale.items))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sales(
        self, 
        page: int = 1, 
        limit: int = 50,
        start_date: str = None,
        end_date: str = None
    ) -> tuple[List[Sale], int]:
        """List sales with pagination and optional date filters."""
        stmt = select(Sale).options(selectinload(Sale.items)).order_by(Sale.created_at.desc())
        
        # Apply date filters if provided - convert strings to datetime
        if start_date:
            # Parse date string and set to start of day (00:00:00)
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            stmt = stmt.where(Sale.created_at >= start_datetime)
        if end_date:
            # Parse date string and set to end of day (23:59:59)
            end_datetime = datetime.combine(
                datetime.strptime(end_date, "%Y-%m-%d").date(),
                time(23, 59, 59)
            )
            stmt = stmt.where(Sale.created_at <= end_datetime)
        
        # Get total count
        count_stmt = select(func.count(Sale.id))
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            count_stmt = count_stmt.where(Sale.created_at >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(
                datetime.strptime(end_date, "%Y-%m-%d").date(),
                time(23, 59, 59)
            )
            count_stmt = count_stmt.where(Sale.created_at <= end_datetime)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar()
        
        # Get paginated results
        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await self.session.execute(stmt)
        sales = result.scalars().all()
        
        return sales, total

    async def update_sale_status(self, sale_number: str, status: str, ledger_entry_id: str = None) -> Optional[Sale]:
        """Update sale sync status and ledger reference."""
        sale = await self.get_sale(sale_number)
        if sale:
            sale.status = status
            if ledger_entry_id:
                sale.ledger_entry_id = ledger_entry_id
            await self.session.commit()
            await self.session.refresh(sale)
        return sale
