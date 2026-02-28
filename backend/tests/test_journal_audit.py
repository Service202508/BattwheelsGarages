"""
Journal Audit Trail Tests (Sprint 4B-05)
==========================================
Verify that journal_audit_log entries are created on CREATE and REVERSE.
Tests require a running MongoDB instance.
"""
import os
import sys
import subprocess
import pytest

# Set env vars BEFORE any service imports (audit_log.py reads at import time)
if not os.environ.get("MONGO_URL"):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio


def get_db():
    """Get a direct MongoDB connection for assertions."""
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "battwheels_dev")
    client = AsyncIOMotorClient(mongo_url)
    return client[db_name]


def run_async(coro):
    """Run an async coroutine in a sync test."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ==================== AUDIT LOG TESTS ====================

class TestJournalCreateAudit:

    def test_journal_create_generates_audit_entry(self):
        """Creating a journal entry should produce a CREATE audit log record."""
        async def _test():
            db = get_db()
            from services.double_entry_service import DoubleEntryService
            svc = DoubleEntryService(db)
            org_id = "dev-internal-testing-001"

            # Ensure system accounts exist
            await svc.ensure_system_accounts(org_id)
            accounts = await db.chart_of_accounts.find(
                {"organization_id": org_id}, {"_id": 0}
            ).to_list(10)
            if len(accounts) < 2:
                pytest.skip("Insufficient accounts in dev org for journal test")

            acc_a = accounts[0]["account_id"]
            acc_b = accounts[1]["account_id"]

            lines = [
                {"account_id": acc_a, "debit_amount": 500, "credit_amount": 0, "description": "Test debit"},
                {"account_id": acc_b, "debit_amount": 0, "credit_amount": 500, "description": "Test credit"},
            ]
            success, msg, entry = await svc.create_journal_entry(
                organization_id=org_id,
                entry_date="2026-01-15",
                description="4B-05 audit test CREATE",
                lines=lines,
                created_by="test-4b05"
            )
            assert success, f"Journal entry creation failed: {msg}"

            entry_id = entry.get("entry_id")
            assert entry_id, "No entry_id returned"

            # Check audit log
            audit = await db.journal_audit_log.find_one(
                {"journal_entry_id": entry_id, "action": "CREATE"},
                {"_id": 0}
            )
            assert audit is not None, f"No CREATE audit entry for {entry_id}"
            assert audit["action"] == "CREATE"
            assert audit["organization_id"] == org_id
            assert "performed_at" in audit
            assert "audit_id" in audit

            # Cleanup
            await db.journal_entries.delete_one({"entry_id": entry_id})
            await db.journal_audit_log.delete_many({"journal_entry_id": entry_id})

        run_async(_test())


class TestJournalReverseAudit:

    def test_journal_reverse_generates_audit_entry(self):
        """Reversing a journal entry should produce both CREATE and REVERSE audit log records."""
        async def _test():
            db = get_db()
            from services.double_entry_service import DoubleEntryService
            svc = DoubleEntryService(db)
            org_id = "dev-internal-testing-001"

            await svc.ensure_system_accounts(org_id)
            accounts = await db.chart_of_accounts.find(
                {"organization_id": org_id}, {"_id": 0}
            ).to_list(10)
            if len(accounts) < 2:
                pytest.skip("Insufficient accounts in dev org for journal test")

            acc_a = accounts[0]["account_id"]
            acc_b = accounts[1]["account_id"]

            lines = [
                {"account_id": acc_a, "debit_amount": 750, "credit_amount": 0, "description": "Test debit"},
                {"account_id": acc_b, "debit_amount": 0, "credit_amount": 750, "description": "Test credit"},
            ]
            success, msg, entry = await svc.create_journal_entry(
                organization_id=org_id,
                entry_date="2026-01-20",
                description="4B-05 audit test REVERSE",
                lines=lines,
                created_by="test-4b05"
            )
            assert success, f"Create failed: {msg}"
            entry_id = entry.get("entry_id")

            # Reverse
            rev_success, rev_msg, rev_entry = await svc.reverse_journal_entry(
                organization_id=org_id,
                entry_id=entry_id,
                reversal_date="2026-01-21",
                created_by="test-4b05",
                reason="4B-05 test reversal"
            )
            assert rev_success, f"Reverse failed: {rev_msg}"

            # Check: CREATE audit for original
            create_audit = await db.journal_audit_log.find_one(
                {"journal_entry_id": entry_id, "action": "CREATE"},
                {"_id": 0}
            )
            assert create_audit is not None, "Missing CREATE audit for original entry"

            # Check: REVERSE audit
            reverse_audit = await db.journal_audit_log.find_one(
                {"action": "REVERSE", "original_entry_id": entry_id},
                {"_id": 0}
            )
            assert reverse_audit is not None, "Missing REVERSE audit for reversal"
            assert reverse_audit["original_entry_id"] == entry_id

            # Check: CREATE audit for the reversal entry itself
            rev_entry_id = rev_entry.get("entry_id")
            rev_create_audit = await db.journal_audit_log.find_one(
                {"journal_entry_id": rev_entry_id, "action": "CREATE"},
                {"_id": 0}
            )
            assert rev_create_audit is not None, "Missing CREATE audit for reversal entry"

            # Cleanup
            await db.journal_entries.delete_many(
                {"entry_id": {"$in": [entry_id, rev_entry_id]}}
            )
            await db.journal_audit_log.delete_many(
                {"journal_entry_id": {"$in": [entry_id, rev_entry_id]}}
            )
            await db.journal_audit_log.delete_many(
                {"original_entry_id": entry_id}
            )

        run_async(_test())


class TestAuditLogImmutability:

    def test_no_delete_or_update_routes_for_audit_log(self):
        """No route file should contain DELETE or UPDATE operations for journal_audit_log."""
        routes_dir = os.path.join(os.path.dirname(__file__), "..", "routes")
        # Search all route files for any mutation of journal_audit_log
        result = subprocess.run(
            ["grep", "-rn", "journal_audit_log", routes_dir],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        violations = []
        for line in lines:
            lower = line.lower()
            if any(op in lower for op in ["delete_one", "delete_many", "update_one", "update_many", "replace_one", "find_one_and_update", "find_one_and_delete", "find_one_and_replace"]):
                violations.append(line.strip())

        assert len(violations) == 0, (
            f"Found {len(violations)} route(s) that mutate journal_audit_log (must be APPEND-ONLY):\n"
            + "\n".join(violations)
        )
