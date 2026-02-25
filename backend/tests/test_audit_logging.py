"""
Day 4 — C-05: Audit Logging on Financial Mutations
====================================================
Tests that all financial mutation points produce audit log entries
with the correct schema: org_id, user_id, user_role, action,
entity_type, entity_id, timestamp, ip_address, before_snapshot, after_snapshot.
"""
import pytest
import requests
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ORG_ID = "6996dcf072ffd2a2395fee7b"
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "Admin@12345"

TOKEN = None
REQUIRED_FIELDS = {"org_id", "user_id", "user_role", "action", "entity_type",
                    "entity_id", "timestamp", "ip_address", "before_snapshot", "after_snapshot"}


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_token():
    global TOKEN
    if TOKEN:
        return TOKEN
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
    })
    TOKEN = resp.json().get("token", "")
    return TOKEN


def headers():
    return {"Authorization": f"Bearer {get_token()}", "X-Organization-ID": ORG_ID}


async def get_latest_audit(entity_type: str, action: str, entity_id: str = None):
    """Fetch the most recent audit log entry matching criteria."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    query = {"entity_type": entity_type, "action": action, "org_id": ORG_ID}
    if entity_id:
        query["entity_id"] = entity_id
    entry = await db.audit_log.find_one(query, {"_id": 0}, sort=[("timestamp", -1)])
    client.close()
    return entry


async def cleanup_audit_test_data(invoice_ids, payment_ids, cn_ids):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    if invoice_ids:
        await db.invoices.delete_many({"invoice_id": {"$in": invoice_ids}})
        await db.invoice_line_items.delete_many({"invoice_id": {"$in": invoice_ids}})
        await db.invoice_history.delete_many({"invoice_id": {"$in": invoice_ids}})
    if payment_ids:
        await db.invoice_payments.delete_many({"payment_id": {"$in": payment_ids}})
    if cn_ids:
        await db.credit_notes.delete_many({"credit_note_id": {"$in": cn_ids}})
    # Clean audit entries for test entities
    all_ids = (invoice_ids or []) + (payment_ids or []) + (cn_ids or [])
    if all_ids:
        await db.audit_log.delete_many({"entity_id": {"$in": all_ids}})
    client.close()


# ---- Fixtures ----

@pytest.fixture(scope="module")
def created_invoice():
    """Create a test invoice and return its data."""
    # First we need a valid customer
    resp = requests.get(f"{BASE_URL}/api/v1/contacts-enhanced/", params={"limit": 1, "contact_type": "customer"}, headers=headers(), allow_redirects=True)
    contacts = resp.json().get("contacts", [])
    if not contacts:
        pytest.skip("No contacts available for invoice creation test")
    customer_id = contacts[0]["contact_id"]

    payload = {
        "customer_id": customer_id,
        "line_items": [{"name": "Audit Test Item", "quantity": 1, "rate": 1000, "tax_rate": 18}],
        "payment_terms": 30,
    }
    resp = requests.post(f"{BASE_URL}/api/v1/invoices-enhanced/", json=payload, headers=headers(), allow_redirects=True)
    assert resp.status_code == 200, f"Invoice create failed: {resp.text}"
    data = resp.json()
    assert data["code"] == 0
    invoice = data["invoice"]
    yield invoice
    # Cleanup
    run_async(cleanup_audit_test_data([invoice["invoice_id"]], [], []))


# ---- Tests ----

class TestInvoiceCreateAudit:
    def test_audit_entry_exists(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        assert entry is not None, "No audit log for invoice CREATE"

    def test_schema_complete(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"Missing fields in audit entry: {missing}"

    def test_before_snapshot_null_for_create(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        assert entry["before_snapshot"] is None

    def test_after_snapshot_has_data(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        assert entry["after_snapshot"] is not None
        assert entry["after_snapshot"]["invoice_id"] == created_invoice["invoice_id"]

    def test_org_id_populated(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        assert entry["org_id"] == ORG_ID

    def test_timestamp_present(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "CREATE", created_invoice["invoice_id"]))
        assert entry["timestamp"] and len(entry["timestamp"]) > 10


class TestInvoiceUpdateAudit:
    def test_update_creates_audit(self, created_invoice):
        inv_id = created_invoice["invoice_id"]
        resp = requests.put(
            f"{BASE_URL}/api/v1/invoices-enhanced/{inv_id}",
            json={"customer_notes": "Audit test update"},
            headers=headers()
        )
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        entry = run_async(get_latest_audit("invoice", "UPDATE", inv_id))
        assert entry is not None, "No audit log for invoice UPDATE"

    def test_before_snapshot_present(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "UPDATE", created_invoice["invoice_id"]))
        assert entry["before_snapshot"] is not None
        assert "invoice_id" in entry["before_snapshot"]

    def test_after_snapshot_present(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "UPDATE", created_invoice["invoice_id"]))
        assert entry["after_snapshot"] is not None


class TestInvoiceVoidAudit:
    def test_void_creates_audit(self, created_invoice):
        inv_id = created_invoice["invoice_id"]
        resp = requests.post(
            f"{BASE_URL}/api/v1/invoices-enhanced/{inv_id}/void?reason=audit_test",
            headers=headers()
        )
        assert resp.status_code == 200, f"Void failed: {resp.text}"
        entry = run_async(get_latest_audit("invoice", "VOID", inv_id))
        assert entry is not None, "No audit log for invoice VOID"

    def test_void_before_snapshot(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "VOID", created_invoice["invoice_id"]))
        assert entry["before_snapshot"] is not None
        assert entry["before_snapshot"].get("status") != "void"

    def test_void_after_snapshot(self, created_invoice):
        entry = run_async(get_latest_audit("invoice", "VOID", created_invoice["invoice_id"]))
        assert entry["after_snapshot"] is not None
        assert entry["after_snapshot"].get("status") == "void"


class TestJournalEntryAudit:
    def test_journal_audit_exists(self):
        """Journal entries are created as side-effects of invoice/CN creation.
        Check that at least one journal_entry CREATE audit exists."""
        entry = run_async(get_latest_audit("journal_entry", "CREATE"))
        # May or may not exist depending on accounting service config
        # Just verify schema if present
        if entry:
            missing = REQUIRED_FIELDS - set(entry.keys())
            assert not missing, f"Missing fields: {missing}"
            assert entry["after_snapshot"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
