"""
Fulfillment API routes — /api/v1/fulfillment
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.rate_limit import limiter
from app.schemas import CreateFulfillmentRequest
from app.services import fulfillment as fulfillment_service
from app.models import APIKey
from app.services.auth import validate_api_key
router = APIRouter(
    prefix="/api/v1/fulfillment", 
    tags=["Fulfillment"]
)


@router.post("/orders")
@limiter.limit(lambda: settings.RATE_LIMIT_AMAZON)
async def create_order(
    request: Request,
    body: CreateFulfillmentRequest, 
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(validate_api_key)
):
    """Create MCF fulfillment order. Respects DRY_RUN setting."""
    result = await fulfillment_service.create_fulfillment_order(body, db)
    return result


@router.get("/orders")
@limiter.limit(lambda: settings.RATE_LIMIT_STANDARD)
async def list_orders(
    request: Request,
    status: str | None = None, 
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(validate_api_key)
):
    """List all tracked fulfillment orders. Optional ?status= filter."""
    return await fulfillment_service.list_fulfillment_orders(db, status=status)


@router.get("/orders/{order_id}", include_in_schema=False)
@limiter.limit(lambda: settings.RATE_LIMIT_STANDARD)
async def get_order(
    request: Request,
    order_id: str, 
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(validate_api_key)
):
    """Get details of a specific fulfillment order."""
    result = await fulfillment_service.get_fulfillment_order(order_id, db)
    if not result:
        return {"error": "Order not found", "order_id": order_id}
    return result


@router.delete("/orders/{order_id}", include_in_schema=False)
@limiter.limit(lambda: settings.RATE_LIMIT_AMAZON)
async def cancel_order(
    request: Request,
    order_id: str, 
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(validate_api_key)
):
    """Cancel a fulfillment order (only if in Received/Planning status)."""
    return await fulfillment_service.cancel_fulfillment_order(order_id, db)
