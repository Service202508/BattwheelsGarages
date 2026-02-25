# Findings Tracker
## Active findings discovered during Week 1 remediation

### H-NEW-01 (HIGH) — Unscoped `organization_settings` query in GST module
- **File:** `backend/routes/gst.py` line 715
- **Issue:** `organization_settings.find_one({})` returns the first org's settings regardless of caller. Must be scoped by `organization_id`.
- **Discovered:** Day 3 (C-06 fix)
- **Scheduled:** Week 2

### M-NEW-02 (MEDIUM) — `user_role` empty in audit entries
- **File:** `backend/utils/audit_log.py` (consumer), `core/tenant/guard.py` (source)
- **Issue:** `TenantGuardMiddleware` sets `request.state.tenant_user_id` but does not set `request.state.user_role`. Audit log entries have empty `user_role` field.
- **Discovered:** Day 4 (C-05 fix)
- **Scheduled:** Week 2
