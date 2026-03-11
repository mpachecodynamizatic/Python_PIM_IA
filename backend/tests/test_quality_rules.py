"""Tests for Quality Rules CRUD and scoring engine with rules."""
import pytest

pytestmark = pytest.mark.asyncio

SETS_URL = "/api/v1/quality-rules/sets"


async def _create_product(client, auth_headers, sku="QR-001"):
    """Create a minimal product for quality testing."""
    cat = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "QR Cat", "slug": "qr-cat"},
        headers=auth_headers,
    )
    cat_id = cat.json()["id"]
    await client.post(
        "/api/v1/products",
        json={"sku": sku, "brand": "TestBrand", "category_id": cat_id},
        headers=auth_headers,
    )
    return sku, cat_id


# ── CRUD Rule Sets ──────────────────────────────────────────────────

async def test_create_rule_set(client, auth_headers):
    resp = await client.post(
        SETS_URL,
        json={"name": "Test Set", "description": "For testing"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Set"
    assert data["active"] is False
    assert data["rules"] == []


async def test_create_rule_set_with_inline_rules(client, auth_headers):
    resp = await client.post(
        SETS_URL,
        json={
            "name": "Inline Set",
            "rules": [
                {"dimension": "media", "weight": 2.0, "min_score": 0.5},
                {"dimension": "seo", "weight": 1.5},
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["rules"]) == 2
    dims = {r["dimension"] for r in data["rules"]}
    assert dims == {"media", "seo"}


async def test_list_rule_sets(client, auth_headers):
    await client.post(SETS_URL, json={"name": "Set A"}, headers=auth_headers)
    await client.post(SETS_URL, json={"name": "Set B"}, headers=auth_headers)
    resp = await client.get(SETS_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_get_rule_set(client, auth_headers):
    create = await client.post(SETS_URL, json={"name": "Detail Set"}, headers=auth_headers)
    set_id = create.json()["id"]
    resp = await client.get(f"{SETS_URL}/{set_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail Set"


async def test_delete_rule_set(client, auth_headers):
    create = await client.post(SETS_URL, json={"name": "To Delete"}, headers=auth_headers)
    set_id = create.json()["id"]
    resp = await client.delete(f"{SETS_URL}/{set_id}", headers=auth_headers)
    assert resp.status_code in (200, 204)
    # Verify gone
    get_resp = await client.get(f"{SETS_URL}/{set_id}", headers=auth_headers)
    assert get_resp.status_code == 404


# ── Activate / Deactivate ──────────────────────────────────────────

async def test_activate_rule_set(client, auth_headers):
    a = await client.post(SETS_URL, json={"name": "Set A"}, headers=auth_headers)
    b = await client.post(SETS_URL, json={"name": "Set B"}, headers=auth_headers)
    a_id = a.json()["id"]
    b_id = b.json()["id"]

    # Activate A
    resp = await client.post(f"{SETS_URL}/{a_id}/activate", headers=auth_headers)
    assert resp.status_code in (200, 204)

    # A is active, B is not
    sets = (await client.get(SETS_URL, headers=auth_headers)).json()
    active = [s for s in sets if s["active"]]
    assert len(active) == 1
    assert active[0]["id"] == a_id

    # Activate B → A becomes inactive
    await client.post(f"{SETS_URL}/{b_id}/activate", headers=auth_headers)
    sets = (await client.get(SETS_URL, headers=auth_headers)).json()
    active = [s for s in sets if s["active"]]
    assert len(active) == 1
    assert active[0]["id"] == b_id


async def test_deactivate_all(client, auth_headers):
    a = await client.post(SETS_URL, json={"name": "Active Set"}, headers=auth_headers)
    await client.post(f"{SETS_URL}/{a.json()['id']}/activate", headers=auth_headers)

    resp = await client.post(f"{SETS_URL}/deactivate-all", headers=auth_headers)
    assert resp.status_code in (200, 204)

    sets = (await client.get(SETS_URL, headers=auth_headers)).json()
    assert all(not s["active"] for s in sets)


# ── CRUD Rules ──────────────────────────────────────────────────────

async def test_add_and_delete_rule(client, auth_headers):
    create = await client.post(SETS_URL, json={"name": "Rules Test"}, headers=auth_headers)
    set_id = create.json()["id"]

    # Add rule
    rule_resp = await client.post(
        f"{SETS_URL}/{set_id}/rules",
        json={"dimension": "brand", "weight": 3.0, "min_score": 0.8},
        headers=auth_headers,
    )
    assert rule_resp.status_code == 201
    rule_id = rule_resp.json()["id"]

    # Verify listed
    rules = (await client.get(f"{SETS_URL}/{set_id}/rules", headers=auth_headers)).json()
    assert len(rules) == 1

    # Delete
    del_resp = await client.delete(f"/api/v1/quality-rules/rules/{rule_id}", headers=auth_headers)
    assert del_resp.status_code in (200, 204)

    # Verify gone
    rules = (await client.get(f"{SETS_URL}/{set_id}/rules", headers=auth_headers)).json()
    assert len(rules) == 0


# ── Scoring Engine with Rules ──────────────────────────────────────

async def test_quality_with_active_rules(client, auth_headers):
    """When rules are active, overall should use weighted calculation."""
    sku, _ = await _create_product(client, auth_headers)

    # Create rule set with media weight=3 (which is 0 for our product)
    rs = await client.post(
        SETS_URL,
        json={
            "name": "Heavy Media",
            "rules": [
                {"dimension": "media", "weight": 3.0, "min_score": 0.0},
                {"dimension": "brand", "weight": 1.0},
                {"dimension": "category", "weight": 1.0},
            ],
        },
        headers=auth_headers,
    )
    set_id = rs.json()["id"]
    await client.post(f"{SETS_URL}/{set_id}/activate", headers=auth_headers)

    # Get quality
    q = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)
    assert q.status_code == 200
    data = q.json()
    assert "rule_set" in data
    assert data["rule_set"]["id"] == set_id
    # Dimensions without explicit rules get default weight 1.0:
    # brand=1*1 + category=1*1 + seo=0*1 + attributes=0*1 + media=0*3 + i18n=0*1 = 2
    # total_weight = 1+1+1+1+3+1 = 8 → overall = 2/8 * 100 = 25.0
    assert data["overall"] == 25.0


async def test_quality_with_min_score_violation(client, auth_headers):
    """When min_score threshold is not met, dimension counts as 0."""
    sku, _ = await _create_product(client, auth_headers, sku="QR-V01")

    rs = await client.post(
        SETS_URL,
        json={
            "name": "Strict SEO",
            "rules": [
                {"dimension": "seo", "weight": 1.0, "min_score": 1.0},
            ],
        },
        headers=auth_headers,
    )
    set_id = rs.json()["id"]
    await client.post(f"{SETS_URL}/{set_id}/activate", headers=auth_headers)

    q = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)
    data = q.json()
    # SEO is 0 (no seo data), min_score=1.0 → violation
    assert "violations" in data
    assert "seo" in data["violations"]


async def test_quality_report_shows_active_ruleset(client, auth_headers):
    """Quality report includes active_rule_set info."""
    await _create_product(client, auth_headers, sku="QR-RPT")

    rs = await client.post(
        SETS_URL, json={"name": "Report Set"}, headers=auth_headers,
    )
    set_id = rs.json()["id"]
    await client.post(f"{SETS_URL}/{set_id}/activate", headers=auth_headers)

    report = await client.get("/api/v1/quality/report", headers=auth_headers)
    data = report.json()
    assert data["active_rule_set"] is not None
    assert data["active_rule_set"]["id"] == set_id


async def test_quality_default_without_rules(client, auth_headers):
    """Without active rules, uses default arithmetic mean."""
    sku, _ = await _create_product(client, auth_headers, sku="QR-DEF")

    # Ensure no active set
    await client.post(f"{SETS_URL}/deactivate-all", headers=auth_headers)

    q = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)
    data = q.json()
    # brand=1, category=1, seo=0, attributes=0, media=0, i18n=0 → 2/6 * 100 = 33.3
    assert data["overall"] == 33.3
    assert data.get("rule_set") is None


# ── Simulation ──────────────────────────────────────────────────────

async def test_simulate_rule_set(client, auth_headers):
    """Simulation endpoint compares current vs hypothetical scores."""
    sku, _ = await _create_product(client, auth_headers, sku="QR-SIM")

    # Ensure no active set → default scoring
    await client.post(f"{SETS_URL}/deactivate-all", headers=auth_headers)

    # Create a set to simulate (not activated)
    rs = await client.post(
        SETS_URL,
        json={
            "name": "Simulated",
            "rules": [
                {"dimension": "brand", "weight": 5.0},
                {"dimension": "category", "weight": 5.0},
            ],
        },
        headers=auth_headers,
    )
    set_id = rs.json()["id"]

    resp = await client.get(f"/api/v1/quality/simulate/{set_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_set"]["id"] == set_id
    assert data["compared_to"] is None  # no active set
    assert len(data["items"]) >= 1
    item = next(i for i in data["items"] if i["sku"] == sku)
    assert "current_overall" in item
    assert "simulated_overall" in item
    assert "diff" in item


async def test_simulate_nonexistent_set(client, auth_headers):
    resp = await client.get(
        "/api/v1/quality/simulate/nonexistent-id", headers=auth_headers,
    )
    assert resp.status_code == 404
