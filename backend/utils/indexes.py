"""Compound index migration. Safe to run on every startup — skips indexes that already exist."""
import logging

logger = logging.getLogger(__name__)


async def ensure_compound_indexes(db):
    """Create all compound indexes. Idempotent."""
    logger.info("Ensuring compound indexes...")

    await db.tickets.create_index(
        [("organization_id", 1), ("status", 1), ("created_at", -1)],
        name="tickets_org_status_date", background=True)
    await db.tickets.create_index(
        [("organization_id", 1), ("assigned_technician_id", 1), ("status", 1)],
        name="tickets_org_assignee_status", background=True)
    await db.tickets.create_index(
        [("organization_id", 1), ("customer_id", 1)],
        name="tickets_org_contact", background=True)

    await db.invoices.create_index(
        [("organization_id", 1), ("status", 1), ("created_at", -1)],
        name="invoices_org_status_date", background=True)
    await db.invoices.create_index(
        [("organization_id", 1), ("customer_id", 1)],
        name="invoices_org_contact", background=True)

    await db.journal_entries.create_index(
        [("organization_id", 1), ("created_at", -1)],
        name="journal_entries_org_date", background=True)
    await db.journal_entries.create_index(
        [("organization_id", 1), ("debit_account", 1), ("created_at", -1)],
        name="journal_entries_org_debit_date", background=True)
    await db.journal_entries.create_index(
        [("organization_id", 1), ("credit_account", 1), ("created_at", -1)],
        name="journal_entries_org_credit_date", background=True)

    await db.contacts.create_index(
        [("organization_id", 1), ("name", 1)],
        name="contacts_org_name", background=True)
    await db.contacts.create_index(
        [("organization_id", 1), ("phone", 1)],
        name="contacts_org_phone", background=True)

    await db.inventory.create_index(
        [("organization_id", 1), ("quantity", 1)],
        name="inventory_org_qty", background=True)

    await db.employees.create_index(
        [("organization_id", 1), ("status", 1)],
        name="employees_org_status", background=True)

    await db.audit_logs.create_index(
        [("organization_id", 1), ("timestamp", -1)],
        name="audit_logs_org_ts", background=True)
    await db.audit_logs.create_index(
        [("organization_id", 1), ("resource_type", 1), ("resource_id", 1)],
        name="audit_logs_org_resource", background=True)

    await db.efi_platform_patterns.create_index(
        [("vehicle_model", 1), ("confidence_score", -1)],
        name="efi_patterns_model_conf", background=True)

    await db.sequences.create_index(
        [("sequence_id", 1)],
        unique=True, name="sequences_id_unique", background=True)

    await db.password_reset_tokens.create_index(
        "expires_at", expireAfterSeconds=0, name="reset_tokens_ttl")

    await db.payroll_runs.create_index(
        [("organization_id", 1), ("period", 1)],
        unique=True, name="payroll_org_period_unique", background=True)

    logger.info("Compound indexes ensured")
