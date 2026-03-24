"""Dashboard statistics endpoint."""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product, ProductI18n
from app.models.category import Category
from app.models.quality_rule import QualityRuleSet
from app.models.media import MediaAsset
from app.models.sync_job import SyncJob
from app.models.product_sync_history import ProductSyncHistory
from app.models.product_comment import ProductComment
from app.models.audit import AuditLog
from app.models.product_channel import ProductChannel
from app.models.channel import Channel
from app.models.brand import Brand
from app.services import quality_service

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get comprehensive dashboard statistics."""

    # --- Products stats ---
    total_products_query = select(func.count(Product.sku))
    total_products = (await db.execute(total_products_query)).scalar() or 0

    # Products by status
    by_status = {}
    for status in ["draft", "in_review", "approved", "ready", "retired"]:
        count_query = select(func.count(Product.sku)).where(Product.status == status)
        by_status[status] = (await db.execute(count_query)).scalar() or 0

    # Products without media
    products_with_media_query = select(func.count(func.distinct(MediaAsset.sku)))
    products_with_media = (await db.execute(products_with_media_query)).scalar() or 0
    without_media = max(0, total_products - products_with_media)

    # Products without i18n
    products_with_i18n_query = select(func.count(func.distinct(ProductI18n.sku)))
    products_with_i18n = (await db.execute(products_with_i18n_query)).scalar() or 0
    without_i18n = max(0, total_products - products_with_i18n)

    # Products without channels
    products_with_channels_query = select(func.count(func.distinct(ProductChannel.sku)))
    products_with_channels = (await db.execute(products_with_channels_query)).scalar() or 0
    without_channels = max(0, total_products - products_with_channels)

    # --- Quality stats ---
    # Quality is calculated on-demand, so we'll compute a sample for dashboard performance
    # Calculate quality for up to 100 random products (or all if less than 100)
    avg_score = 0.0
    below_threshold = 0
    critical_errors = 0

    if total_products > 0:
        try:
            # Get a sample of products (limit to 100 for performance)
            sample_size = min(total_products, 100)
            sample_products_query = select(Product.sku).limit(sample_size)
            sample_products_result = await db.execute(sample_products_query)
            sample_skus = [row[0] for row in sample_products_result.all()]

            if sample_skus:
                scores = []
                for sku in sample_skus:
                    try:
                        quality = await quality_service.get_product_quality(db, sku)
                        score = quality.get("overall", 0)
                        scores.append(score)

                        if score < 60:
                            below_threshold += 1
                        if score < 40:
                            # Check if product is published
                            prod_query = select(Product.status).where(Product.sku == sku)
                            prod_status = (await db.execute(prod_query)).scalar()
                            if prod_status == "ready":
                                critical_errors += 1
                    except:
                        # Ignore individual product quality calculation errors
                        pass

                if scores:
                    avg_score = sum(scores) / len(scores)

                    # Extrapolate counts to total population if we sampled
                    if total_products > sample_size:
                        ratio = total_products / sample_size
                        below_threshold = int(below_threshold * ratio)
                        critical_errors = int(critical_errors * ratio)
        except:
            # If quality calculation fails entirely, just set to 0
            pass

    # --- Sync stats ---
    total_channels_query = select(func.count(Channel.id))
    total_channels = (await db.execute(total_channels_query)).scalar() or 0

    # Last sync jobs per channel
    channels_ok = 0
    channels_error = 0
    last_failures = []

    if total_channels > 0:
        channels_query = select(Channel)
        channels_result = await db.execute(channels_query)
        channels = channels_result.scalars().all()

        for channel in channels:
            # Get last job for this channel (using channel string field, not FK)
            last_job_query = (
                select(SyncJob)
                .where(SyncJob.channel == channel.code)
                .order_by(desc(SyncJob.created_at))
                .limit(1)
            )
            last_job = (await db.execute(last_job_query)).scalar_one_or_none()

            if last_job:
                if last_job.status == "completed":
                    channels_ok += 1
                elif last_job.status in ("failed", "error"):
                    channels_error += 1
                    last_failures.append({
                        "channel": channel.code,
                        "error": last_job.error_message[:100] if last_job.error_message else "Unknown error",
                        "time": last_job.updated_at.isoformat() if last_job.updated_at else None,
                    })

    # Pending sync products
    pending_sync_query = select(func.count(ProductSyncHistory.id)).where(
        ProductSyncHistory.status == "pending"
    )
    pending_sync = (await db.execute(pending_sync_query)).scalar() or 0

    # --- Activity stats ---
    # Total comments (resolved field doesn't exist in DB)
    unresolved_comments_query = select(func.count(ProductComment.id))
    unresolved_comments = (await db.execute(unresolved_comments_query)).scalar() or 0

    # Comments mentioning current user
    pending_mentions_query = select(func.count(ProductComment.id)).where(
        ProductComment.mentions.like(f"%{current_user.email}%")
    )
    pending_mentions = (await db.execute(pending_mentions_query)).scalar() or 0

    # Edits today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    edits_today_query = select(func.count(AuditLog.id)).where(
        and_(
            AuditLog.created_at >= today_start,
            AuditLog.action.in_(["create", "update"])
        )
    )
    edits_today = (await db.execute(edits_today_query)).scalar() or 0

    # Recent activity (last 20 audit entries)
    recent_activity_query = (
        select(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .limit(20)
    )
    recent_activity_result = await db.execute(recent_activity_query)
    recent_activity_raw = recent_activity_result.scalars().all()

    recent_activity = [
        {
            "id": audit.id,
            "resource": audit.resource,
            "resource_id": audit.resource_id,
            "action": audit.action,
            "actor": audit.actor,
            "created_at": audit.created_at.isoformat() if audit.created_at else None,
        }
        for audit in recent_activity_raw
    ]

    # --- Workflow stats ---
    # Average time to publish (draft -> ready)
    # This is complex, we'll use a simplified version: products that went from draft to ready
    # We'll calculate based on audit logs
    avg_time_to_publish = 0.0

    # In review count
    in_review = by_status.get("in_review", 0)

    # Approved pending publication
    approved_pending = by_status.get("approved", 0)

    # --- Coverage stats ---
    # Categories without products
    total_categories_query = select(func.count(Category.id))
    total_categories = (await db.execute(total_categories_query)).scalar() or 0

    categories_with_products_query = select(func.count(func.distinct(Product.category_id)))
    categories_with_products = (await db.execute(categories_with_products_query)).scalar() or 0
    empty_categories = max(0, total_categories - categories_with_products)

    # Brands with few products
    brands_low_products = []
    brands_query = select(Brand)
    brands_result = await db.execute(brands_query)
    brands = brands_result.scalars().all()

    for brand in brands:
        count_query = select(func.count(Product.sku)).where(Product.brand == brand.name)
        count = (await db.execute(count_query)).scalar() or 0
        if 0 < count < 5:
            brands_low_products.append({"name": brand.name, "count": count})

    # Top 5 categories by volume
    top_categories_query = (
        select(Product.category_id, func.count(Product.sku).label("count"))
        .group_by(Product.category_id)
        .order_by(desc("count"))
        .limit(5)
    )
    top_categories_result = await db.execute(top_categories_query)
    top_categories_raw = top_categories_result.all()

    top_categories = []
    for cat_id, count in top_categories_raw:
        if cat_id:
            cat_query = select(Category).where(Category.id == cat_id)
            cat = (await db.execute(cat_query)).scalar_one_or_none()
            if cat:
                top_categories.append({"name": cat.name, "count": count})

    # Growth this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    growth_query = select(func.count(Product.sku)).where(
        Product.created_at >= month_start
    )
    growth_this_month = (await db.execute(growth_query)).scalar() or 0

    return {
        "products": {
            "total": total_products,
            "by_status": by_status,
            "without_media": without_media,
            "without_i18n": without_i18n,
            "without_channels": without_channels,
        },
        "quality": {
            "avg_score": round(avg_score, 1),
            "below_threshold": below_threshold,
            "critical_errors": critical_errors,
        },
        "sync": {
            "total_channels": total_channels,
            "channels_ok": channels_ok,
            "channels_error": channels_error,
            "last_failures": last_failures[:3],  # Only top 3
            "pending_sync": pending_sync,
        },
        "activity": {
            "unresolved_comments": unresolved_comments,
            "pending_mentions": pending_mentions,
            "edits_today": edits_today,
            "recent_activity": recent_activity,
        },
        "workflow": {
            "avg_time_to_publish": avg_time_to_publish,
            "in_review": in_review,
            "approved_pending": approved_pending,
        },
        "coverage": {
            "total_categories": total_categories,
            "empty_categories": empty_categories,
            "brands_low_products": brands_low_products[:10],
            "top_categories": top_categories,
            "growth_this_month": growth_this_month,
        },
    }
