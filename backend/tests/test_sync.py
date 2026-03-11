"""Tests for Phase 4 multicanal sync: history, retry, scheduling, connectors."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import ConnectorResult, ProductSyncDetail
from app.models.product_sync_history import ProductSyncHistory
from app.models.sync_job import SyncJob
from app.services.sync_service import (
    _compute_next_retry,
    _compute_next_run,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@pytest.fixture
async def sample_category(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "SyncCat", "slug": "sync-cat"},
        headers=auth_headers,
    )
    return resp.json()


@pytest.fixture
async def sample_product(client: AsyncClient, auth_headers, sample_category):
    resp = await client.post(
        "/api/v1/products",
        json={
            "sku": "SYNC-001",
            "brand": "SyncBrand",
            "category_id": sample_category["id"],
        },
        headers=auth_headers,
    )
    return resp.json()


@pytest.fixture
async def ready_product(client: AsyncClient, auth_headers, sample_product):
    """Product transitioned to 'ready' so connectors will export it."""
    resp = await client.post(
        f"/api/v1/products/{sample_product['sku']}/transitions",
        json={"new_status": "ready"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    return resp.json()


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------
class TestHelpers:
    def test_compute_next_retry_backoff(self):
        before = datetime.now(timezone.utc)
        # retry_count=1 → delay = 30 * 2^1 = 60s
        result = _compute_next_retry(1)
        assert result >= before + timedelta(seconds=59)
        assert result <= before + timedelta(seconds=62)

    def test_compute_next_retry_escalates(self):
        r0 = _compute_next_retry(0)
        r1 = _compute_next_retry(1)
        r2 = _compute_next_retry(2)
        # Delays should strictly increase
        now = datetime.now(timezone.utc)
        d0 = (r0 - now).total_seconds()
        d1 = (r1 - now).total_seconds()
        d2 = (r2 - now).total_seconds()
        assert d0 < d1 < d2

    def test_compute_next_run_valid_cron(self):
        result = _compute_next_run("*/5 * * * *")
        assert result is not None
        assert result > datetime.now(timezone.utc)

    def test_compute_next_run_invalid_cron(self):
        result = _compute_next_run("not a cron")
        assert result is None


# ---------------------------------------------------------------------------
# API tests: channels
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_channels(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/sync/channels", headers=auth_headers)
    assert resp.status_code == 200
    channels = resp.json()
    assert isinstance(channels, list)
    assert "csv" in channels
    assert "shopify" in channels
    assert "amazon" in channels
    assert "woocommerce" in channels


# ---------------------------------------------------------------------------
# API tests: create sync job with scheduling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_sync_job_basic(client: AsyncClient, auth_headers, ready_product):
    resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["channel"] == "csv"
    assert data["max_retries"] == 3
    assert data["retry_count"] == 0
    assert data["scheduled"] is False


@pytest.mark.asyncio
async def test_create_sync_job_with_cron(client: AsyncClient, auth_headers, ready_product):
    resp = await client.post(
        "/api/v1/sync/jobs",
        json={
            "channel": "shopify",
            "filters": {},
            "cron_expression": "0 */6 * * *",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["scheduled"] is True
    assert data["cron_expression"] == "0 */6 * * *"
    assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_create_sync_job_with_max_retries(client: AsyncClient, auth_headers, ready_product):
    resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}, "max_retries": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["max_retries"] == 5


@pytest.mark.asyncio
async def test_create_sync_job_invalid_channel(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "nonexistent", "filters": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# API tests: list / get jobs
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_sync_jobs(client: AsyncClient, auth_headers, ready_product):
    await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/sync/jobs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_sync_job(client: AsyncClient, auth_headers, ready_product):
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/sync/jobs/{job_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_sync_job_not_found(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/sync/jobs/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API tests: schedule update
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_schedule(client: AsyncClient, auth_headers, ready_product):
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/sync/jobs/{job_id}/schedule",
        json={"cron_expression": "0 0 * * *", "enabled": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheduled"] is True
    assert data["cron_expression"] == "0 0 * * *"
    assert data["next_run_at"] is not None


@pytest.mark.asyncio
async def test_disable_schedule(client: AsyncClient, auth_headers, ready_product):
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}, "cron_expression": "0 0 * * *"},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/sync/jobs/{job_id}/schedule",
        json={"cron_expression": "0 0 * * *", "enabled": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scheduled"] is False
    assert data["next_run_at"] is None


# ---------------------------------------------------------------------------
# API tests: retry
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retry_sync_job(client: AsyncClient, auth_headers, db_session: AsyncSession, ready_product):
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    # Manually mark the job as failed for retry
    result = await db_session.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one()
    job.status = "failed"
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/sync/jobs/{job_id}/retry",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_retry_not_allowed_for_queued(client: AsyncClient, auth_headers, db_session, ready_product):
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {}},
        headers=auth_headers,
    )
    job_id = create_resp.json()["id"]

    # Mark it queued (it may already be queued or running due to background task)
    result = await db_session.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one()
    job.status = "running"
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/sync/jobs/{job_id}/retry",
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Service tests: run_sync_job records history
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_sync_job_records_history(client: AsyncClient, auth_headers, ready_product):
    """When a sync job runs, it creates ProductSyncHistory records."""
    from tests.conftest import TestSessionLocal

    sku = ready_product["sku"]

    # Create and trigger job via API (background task runs it)
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {"status": "ready"}},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    # Wait for background task to complete
    await asyncio.sleep(2)

    # Check from a fresh session to see committed data
    async with TestSessionLocal() as fresh_db:
        result = await fresh_db.execute(select(SyncJob).where(SyncJob.id == job_id))
        updated_job = result.scalar_one()
        assert updated_job.status in ("done", "failed")

        hist_result = await fresh_db.execute(
            select(ProductSyncHistory).where(ProductSyncHistory.job_id == job_id)
        )
        histories = hist_result.scalars().all()
        if updated_job.status == "done":
            assert len(histories) >= 1
            skus = [h.sku for h in histories]
            assert sku in skus


# ---------------------------------------------------------------------------
# Service tests: auto-retry on failure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_auto_retry_on_failure(db_session: AsyncSession, ready_product):
    """When a connector raises, the job moves to retry_pending with incremented retry_count."""
    from app.services import sync_service
    from app.schemas.sync_job import SyncJobCreate

    job = await sync_service.create_sync_job(
        db_session, SyncJobCreate(channel="csv", filters={}, max_retries=2)
    )
    await db_session.commit()
    job_id = str(job.id)

    # Patch the CSV connector to raise
    with patch("app.services.sync_service.get_connector") as mock_get:
        failing_connector = AsyncMock()
        failing_connector.run = AsyncMock(side_effect=RuntimeError("Simulated failure"))
        mock_get.return_value = failing_connector

        await sync_service.run_sync_job(job_id)
        await asyncio.sleep(0.3)

    # Reload from a fresh session to see committed changes
    from tests.conftest import TestSessionLocal
    async with TestSessionLocal() as fresh_db:
        result = await fresh_db.execute(select(SyncJob).where(SyncJob.id == job_id))
        updated_job = result.scalar_one()
        assert updated_job.status == "retry_pending"
        assert updated_job.retry_count == 1
        assert updated_job.next_retry_at is not None


@pytest.mark.asyncio
async def test_max_retries_exhausted(db_session: AsyncSession, ready_product):
    """After max retries exhausted, job stays as failed."""
    from app.services import sync_service
    from app.schemas.sync_job import SyncJobCreate

    job = await sync_service.create_sync_job(
        db_session, SyncJobCreate(channel="csv", filters={}, max_retries=1)
    )
    # Pre-set retry_count so next failure exhausts retries
    job.retry_count = 1
    await db_session.commit()
    job_id = str(job.id)

    with patch("app.services.sync_service.get_connector") as mock_get:
        failing_connector = AsyncMock()
        failing_connector.run = AsyncMock(side_effect=RuntimeError("Fail"))
        mock_get.return_value = failing_connector

        await sync_service.run_sync_job(job_id)
        await asyncio.sleep(0.3)

    from tests.conftest import TestSessionLocal
    async with TestSessionLocal() as fresh_db:
        result = await fresh_db.execute(select(SyncJob).where(SyncJob.id == job_id))
        updated_job = result.scalar_one()
        assert updated_job.status == "failed"


# ---------------------------------------------------------------------------
# API tests: product sync history
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_product_sync_history_empty(client: AsyncClient, auth_headers, ready_product):
    sku = ready_product["sku"]
    resp = await client.get(
        f"/api/v1/sync/history/product/{sku}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_product_sync_history_after_job(client: AsyncClient, auth_headers, ready_product):
    sku = ready_product["sku"]

    # Run a sync job
    create_resp = await client.post(
        "/api/v1/sync/jobs",
        json={"channel": "csv", "filters": {"status": "ready"}},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    # Wait for background task to complete
    await asyncio.sleep(2)

    resp = await client.get(
        f"/api/v1/sync/history/product/{sku}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Should have history now
    assert data["total"] >= 1
    assert data["items"][0]["sku"] == sku
    assert data["items"][0]["channel"] == "csv"


@pytest.mark.asyncio
async def test_get_product_sync_status(client: AsyncClient, auth_headers, db_session, ready_product):
    sku = ready_product["sku"]

    # Add manual history records for two channels
    h1 = ProductSyncHistory(
        sku=sku, channel="shopify", status="published", detail={}, job_id=None
    )
    h2 = ProductSyncHistory(
        sku=sku, channel="amazon", status="failed", detail={}, error_message="timeout"
    )
    db_session.add_all([h1, h2])
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/sync/history/product/{sku}/status",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    statuses = resp.json()
    channels = {s["channel"]: s["status"] for s in statuses}
    assert channels["shopify"] == "published"
    assert channels["amazon"] == "failed"


@pytest.mark.asyncio
async def test_get_channel_sync_history(client: AsyncClient, auth_headers, db_session, ready_product):
    sku = ready_product["sku"]
    h = ProductSyncHistory(
        sku=sku, channel="woocommerce", status="published", detail={}
    )
    db_session.add(h)
    await db_session.commit()

    resp = await client.get(
        "/api/v1/sync/history/channel/woocommerce",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["channel"] == "woocommerce"


# ---------------------------------------------------------------------------
# Connector tests — use a fresh session to see committed data
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_connectors_registered():
    from app.connectors import list_channels, get_connector
    channels = list_channels()
    assert set(channels) >= {"csv", "http", "shopify", "amazon", "woocommerce"}
    for ch in channels:
        connector = get_connector(ch)
        assert connector is not None


@pytest.mark.asyncio
async def test_shopify_connector_runs(ready_product):
    from app.connectors import get_connector
    from tests.conftest import TestSessionLocal
    connector = get_connector("shopify")
    async with TestSessionLocal() as fresh_db:
        result = await connector.run(fresh_db, {"status": "ready"})
    assert result.total_products >= 1
    assert result.exported >= 1
    assert len(result.product_details) >= 1
    detail = result.product_details[0]
    assert detail.sku == ready_product["sku"]
    assert detail.status == "published"


@pytest.mark.asyncio
async def test_amazon_connector_runs(ready_product):
    from app.connectors import get_connector
    from tests.conftest import TestSessionLocal
    connector = get_connector("amazon")
    async with TestSessionLocal() as fresh_db:
        result = await connector.run(fresh_db, {"status": "ready"})
    assert result.total_products >= 1
    assert result.exported >= 1
    assert len(result.product_details) >= 1


@pytest.mark.asyncio
async def test_woocommerce_connector_runs(ready_product):
    from app.connectors import get_connector
    from tests.conftest import TestSessionLocal
    connector = get_connector("woocommerce")
    async with TestSessionLocal() as fresh_db:
        result = await connector.run(fresh_db, {"status": "ready"})
    assert result.total_products >= 1
    assert result.exported >= 1


@pytest.mark.asyncio
async def test_csv_connector_produces_details(ready_product):
    from app.connectors import get_connector
    from tests.conftest import TestSessionLocal
    connector = get_connector("csv")
    async with TestSessionLocal() as fresh_db:
        result = await connector.run(fresh_db, {"status": "ready"})
    assert result.total_products >= 1
    assert len(result.product_details) >= 1
    for d in result.product_details:
        assert d.status in ("published", "skipped", "failed")


# ---------------------------------------------------------------------------
# Concurrency limiter (semaphore creation)
# ---------------------------------------------------------------------------
def test_channel_semaphore_created():
    from app.services.sync_service import _get_channel_semaphore
    sem = _get_channel_semaphore("test_channel")
    assert isinstance(sem, asyncio.Semaphore)
    # Same channel returns same semaphore
    sem2 = _get_channel_semaphore("test_channel")
    assert sem is sem2
    # Different channel returns different semaphore
    sem3 = _get_channel_semaphore("other_channel")
    assert sem3 is not sem
