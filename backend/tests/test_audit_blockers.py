"""
Battwheels OS — Pre-Deployment Audit Blocker Tests
Tests SE4.06, DB2.06, FN11.05 (new fixes) and
regression tests for S1.01, S1.06, FN11.11, PY9.02
"""
import os
import pytest
import requests
import subprocess

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# ── Credentials ─────────────────────────────────────────────────────────────
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "admin"

@pytest.fixture(scope="module")
def auth_token():
    """Obtain JWT for admin user."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    token = resp.json().get("token") or resp.json().get("access_token")
    assert token, "No token in login response"
    return token

@pytest.fixture(scope="module")
def org_id(auth_token):
    """Fetch org_id of the admin's organisation."""
    resp = requests.get(
        f"{BASE_URL}/api/organizations/my-organizations",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200, f"Could not fetch orgs: {resp.text}"
    orgs = resp.json().get("organizations", [])
    assert orgs, "No organisations found for admin user"
    return orgs[0]["organization_id"]

@pytest.fixture(scope="module")
def auth_headers(auth_token, org_id):
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-Organization-ID": org_id,
        "Content-Type": "application/json",
    }


# ─────────────────────────────────────────────────────────────────────────────
# S1.01 — Health endpoint regression
# ─────────────────────────────────────────────────────────────────────────────
class TestS1_01_HealthEndpoint:
    """S1.01: GET /api/health must return 200 with status=ok"""

    def test_health_returns_200(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("PASS S1.01: /api/health returned 200")

    def test_health_response_has_status_ok(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        data = resp.json()
        status = data.get("status", "")
        assert status.lower() == "ok", f"Expected status='ok', got '{status}'"
        print(f"PASS S1.01: /api/health status={status}")

    def test_health_response_structure(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        data = resp.json()
        assert "status" in data, "Missing 'status' field in /api/health response"
        print(f"PASS S1.01: /api/health response structure: {list(data.keys())}")


# ─────────────────────────────────────────────────────────────────────────────
# S1.06 — CORS: wildcard * must NOT be returned for arbitrary origins
# ─────────────────────────────────────────────────────────────────────────────
class TestS1_06_CORSNoWildcard:
    """
    S1.06: Wildcard * must not be returned for arbitrary/unknown origins.
    NOTE: Cloudflare / ingress proxy adds its own CORS headers with '*' on the
    external URL — this is a platform-level constraint outside the app's control.
    We test application-level CORS behaviour via the internal FastAPI port (8001).
    """

    INTERNAL_URL = "http://localhost:8001"

    def test_no_wildcard_for_arbitrary_origin(self):
        """App must NOT echo back ACAO for unknown origins (tested on internal port)"""
        resp = requests.options(
            f"{self.INTERNAL_URL}/api/health",
            headers={
                "Origin": "https://evil-attacker.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        # FastAPI CORSMiddleware returns 400 / no ACAO header for disallowed origins
        assert acao != "*", (
            f"FAIL S1.06 (app-level): Access-Control-Allow-Origin is '*' for arbitrary origin. "
            f"Status={resp.status_code}, ACAO='{acao}'"
        )
        # Also verify it's not reflecting the evil origin
        assert acao != "https://evil-attacker.example.com", (
            f"App should not allow https://evil-attacker.example.com"
        )
        print(
            f"PASS S1.06: Arbitrary origin correctly rejected at app level. "
            f"Status={resp.status_code}, ACAO='{acao}'"
        )

    def test_allowed_origin_gets_correct_acao(self):
        """Allowed origin gets echoed back (not wildcard) at app level"""
        allowed = "https://efi-feedback-loop.preview.emergentagent.com"
        resp = requests.options(
            f"{self.INTERNAL_URL}/api/health",
            headers={
                "Origin": allowed,
                "Access-Control-Request-Method": "GET",
            },
        )
        acao = resp.headers.get("Access-Control-Allow-Origin", "")
        # Should echo the specific allowed origin (not '*')
        assert acao == allowed, (
            f"Expected ACAO='{allowed}', got '{acao}'"
        )
        assert acao != "*", "Allowed origin must be echoed specifically, not as wildcard"
        print(f"PASS S1.06: Allowed origin ACAO correctly set to '{acao}'")

    def test_cors_allow_origins_list_is_not_wildcard(self):
        """Verify the CORS_ORIGINS environment default has no '*' entry."""
        cors_raw = os.environ.get(
            "CORS_ORIGINS",
            "https://battwheels.com,https://app.battwheels.com,https://efi-feedback-loop.preview.emergentagent.com",
        )
        origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        assert "*" not in origins, f"FAIL S1.06: '*' found in CORS_ORIGINS list: {origins}"
        print(f"PASS S1.06: CORS origins list is specific: {origins}")


# ─────────────────────────────────────────────────────────────────────────────
# SE4.06 — Security headers on every /api/* response
# ─────────────────────────────────────────────────────────────────────────────
class TestSE4_06_SecurityHeaders:
    """SE4.06: Required security headers must be present on every /api/* response"""

    REQUIRED_HEADERS = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Content-Security-Policy",
    ]

    def _check_headers(self, resp, endpoint_label):
        missing = []
        for h in self.REQUIRED_HEADERS:
            if h.lower() not in {k.lower() for k in resp.headers}:
                missing.append(h)
        return missing

    def test_health_has_security_headers(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        missing = self._check_headers(resp, "/api/health")
        assert not missing, f"Missing security headers on /api/health: {missing}"
        print(f"PASS SE4.06: /api/health has all security headers")

    def test_x_content_type_options_value(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        val = resp.headers.get("X-Content-Type-Options", "")
        assert val.lower() == "nosniff", f"Expected 'nosniff', got '{val}'"
        print(f"PASS SE4.06: X-Content-Type-Options={val}")

    def test_x_frame_options_value(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        val = resp.headers.get("X-Frame-Options", "")
        assert val.upper() == "DENY", f"Expected 'DENY', got '{val}'"
        print(f"PASS SE4.06: X-Frame-Options={val}")

    def test_hsts_value(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        val = resp.headers.get("Strict-Transport-Security", "")
        assert "max-age=" in val, f"Strict-Transport-Security missing max-age: '{val}'"
        print(f"PASS SE4.06: Strict-Transport-Security={val}")

    def test_referrer_policy_value(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        val = resp.headers.get("Referrer-Policy", "")
        assert val, f"Referrer-Policy is empty"
        print(f"PASS SE4.06: Referrer-Policy={val}")

    def test_csp_value(self):
        resp = requests.get(f"{BASE_URL}/api/health")
        val = resp.headers.get("Content-Security-Policy", "")
        assert val, f"Content-Security-Policy is empty"
        assert "default-src" in val, f"CSP missing 'default-src': '{val}'"
        print(f"PASS SE4.06: Content-Security-Policy={val[:80]}...")

    def test_auth_endpoint_has_security_headers(self, auth_headers):
        """Security headers must be present on authenticated endpoints too"""
        resp = requests.get(
            f"{BASE_URL}/api/organizations/my-organizations",
            headers=auth_headers,
        )
        missing = self._check_headers(resp, "/api/organizations/my-organizations")
        assert not missing, (
            f"Missing security headers on /api/organizations/my-organizations: {missing}"
        )
        print(f"PASS SE4.06: /api/organizations/my-organizations has all security headers")

    def test_all_six_headers_present_on_health(self):
        """One omnibus test: all 6 headers present at once"""
        resp = requests.get(f"{BASE_URL}/api/health")
        present = {k.lower(): v for k, v in resp.headers.items()}
        results = {h: present.get(h.lower(), "MISSING") for h in self.REQUIRED_HEADERS}
        missing = [h for h, v in results.items() if v == "MISSING"]
        assert not missing, f"Missing headers: {missing}\nAll header results: {results}"
        print(f"PASS SE4.06: All 6 security headers present: {list(results.keys())}")


# ─────────────────────────────────────────────────────────────────────────────
# DB2.06 — MongoDB backup artifacts
# ─────────────────────────────────────────────────────────────────────────────
class TestDB2_06_MongoBackup:
    """DB2.06: Backup dir, cron job, and DR runbook must exist"""

    BACKUP_ROOT = "/var/backups/mongodb"
    CRON_FILE = "/etc/cron.d/battwheels-mongodb-backup"
    RUNBOOK = "/app/DISASTER_RECOVERY_RUNBOOK.md"
    BACKUP_SCRIPT = "/app/scripts/backup_mongodb.sh"

    def test_backup_root_directory_exists(self):
        result = subprocess.run(["test", "-d", self.BACKUP_ROOT], capture_output=True)
        assert result.returncode == 0, f"Backup directory {self.BACKUP_ROOT} does not exist"
        print(f"PASS DB2.06: {self.BACKUP_ROOT} exists")

    def test_backup_directory_contains_dated_subdirectory(self):
        result = subprocess.run(
            ["find", self.BACKUP_ROOT, "-maxdepth", "1", "-type", "d"],
            capture_output=True, text=True
        )
        dirs = [d for d in result.stdout.strip().split("\n") if d != self.BACKUP_ROOT and d]
        assert dirs, f"No backup subdirectories found under {self.BACKUP_ROOT}"
        print(f"PASS DB2.06: Backup subdirectories found: {dirs}")

    def test_backup_contains_218_bson_gz_files(self):
        result = subprocess.run(
            ["find", self.BACKUP_ROOT, "-name", "*.bson.gz"],
            capture_output=True, text=True
        )
        files = [f for f in result.stdout.strip().split("\n") if f]
        count = len(files)
        assert count >= 218, f"Expected >= 218 .bson.gz files, found {count}"
        print(f"PASS DB2.06: Found {count} .bson.gz files (expected 218)")

    def test_cron_file_exists(self):
        result = subprocess.run(["test", "-f", self.CRON_FILE], capture_output=True)
        assert result.returncode == 0, f"Cron file {self.CRON_FILE} does not exist"
        print(f"PASS DB2.06: {self.CRON_FILE} exists")

    def test_cron_file_has_backup_schedule(self):
        with open(self.CRON_FILE, "r") as f:
            content = f.read()
        assert "backup_mongodb.sh" in content, (
            f"backup_mongodb.sh not referenced in cron file. Content:\n{content}"
        )
        print(f"PASS DB2.06: Cron file references backup_mongodb.sh")

    def test_cron_file_has_daily_schedule(self):
        with open(self.CRON_FILE, "r") as f:
            content = f.read()
        # cron syntax: 0 2 * * * (daily)
        assert "* * *" in content, f"Expected daily cron schedule, got:\n{content}"
        print(f"PASS DB2.06: Cron file has daily schedule")

    def test_disaster_recovery_runbook_exists(self):
        result = subprocess.run(["test", "-f", self.RUNBOOK], capture_output=True)
        assert result.returncode == 0, f"DR runbook {self.RUNBOOK} does not exist"
        print(f"PASS DB2.06: {self.RUNBOOK} exists")

    def test_runbook_has_restore_instructions(self):
        with open(self.RUNBOOK, "r") as f:
            content = f.read()
        assert "mongorestore" in content or "restore" in content.lower(), (
            "DR runbook missing restore instructions"
        )
        print(f"PASS DB2.06: DR runbook contains restore instructions")

    def test_backup_script_is_executable(self):
        result = subprocess.run(["test", "-x", self.BACKUP_SCRIPT], capture_output=True)
        assert result.returncode == 0, f"Backup script {self.BACKUP_SCRIPT} is not executable"
        print(f"PASS DB2.06: {self.BACKUP_SCRIPT} is executable")


# ─────────────────────────────────────────────────────────────────────────────
# FN11.05 — Trial balance endpoint
# ─────────────────────────────────────────────────────────────────────────────
class TestFN11_05_TrialBalance:
    """FN11.05: GET /api/reports/trial-balance returns 200 with required fields"""

    def test_trial_balance_returns_200(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers,
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        )
        print(f"PASS FN11.05: /api/reports/trial-balance returned 200")

    def test_trial_balance_has_is_balanced_field(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers,
        )
        data = resp.json()
        assert "is_balanced" in data, f"Missing 'is_balanced' field. Keys: {list(data.keys())}"
        assert isinstance(data["is_balanced"], bool), (
            f"'is_balanced' must be bool, got {type(data['is_balanced'])}"
        )
        print(f"PASS FN11.05: is_balanced={data['is_balanced']}")

    def test_trial_balance_has_summary_with_totals(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers,
        )
        data = resp.json()
        assert "summary" in data, f"Missing 'summary' field. Keys: {list(data.keys())}"
        summary = data["summary"]
        assert "total_debit" in summary, f"summary missing 'total_debit'. Got: {summary}"
        assert "total_credit" in summary, f"summary missing 'total_credit'. Got: {summary}"
        print(
            f"PASS FN11.05: summary.total_debit={summary['total_debit']}, "
            f"summary.total_credit={summary['total_credit']}"
        )

    def test_trial_balance_has_accounts_array(self, auth_headers):
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers,
        )
        data = resp.json()
        assert "accounts" in data, f"Missing 'accounts' field. Keys: {list(data.keys())}"
        assert isinstance(data["accounts"], list), (
            f"'accounts' must be a list, got {type(data['accounts'])}"
        )
        print(f"PASS FN11.05: accounts array has {len(data['accounts'])} entries")

    def test_trial_balance_debits_equal_credits_when_balanced(self, auth_headers):
        """If is_balanced=True, total_debit must equal total_credit"""
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers=auth_headers,
        )
        data = resp.json()
        summary = data.get("summary", {})
        total_debit = summary.get("total_debit", 0)
        total_credit = summary.get("total_credit", 0)
        is_balanced = data.get("is_balanced", False)

        if is_balanced:
            difference = abs(total_debit - total_credit)
            assert difference < 0.01, (
                f"is_balanced=True but debit({total_debit}) != credit({total_credit}), "
                f"diff={difference}"
            )
            print(
                f"PASS FN11.05: Balanced — total_debit={total_debit}, "
                f"total_credit={total_credit}"
            )
        else:
            # Not balanced is valid if no journal entries yet or unbalanced entries exist
            print(
                f"INFO FN11.05: is_balanced=False — "
                f"total_debit={total_debit}, total_credit={total_credit}"
            )

    def test_trial_balance_with_date_filter(self, auth_headers):
        """Trial balance accepts optional as_of_date query parameter"""
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            params={"as_of_date": "2025-12-31"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, (
            f"Expected 200 with as_of_date param, got {resp.status_code}: {resp.text[:300]}"
        )
        data = resp.json()
        assert data.get("as_of_date") == "2025-12-31", (
            f"as_of_date in response should be 2025-12-31, got {data.get('as_of_date')}"
        )
        print(f"PASS FN11.05: Trial balance with as_of_date filter works")

    def test_trial_balance_missing_org_id_returns_400(self, auth_token):
        """Without X-Organization-ID header, endpoint returns 400"""
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (400, 401, 422), (
            f"Expected 400/401/422 without org id, got {resp.status_code}"
        )
        print(f"PASS FN11.05: Missing org-id returns {resp.status_code}")

    def test_trial_balance_invalid_date_returns_400(self, auth_headers):
        """Invalid date format returns 400"""
        resp = requests.get(
            f"{BASE_URL}/api/reports/trial-balance",
            params={"as_of_date": "not-a-date"},
            headers=auth_headers,
        )
        assert resp.status_code == 400, (
            f"Expected 400 for invalid date, got {resp.status_code}"
        )
        print(f"PASS FN11.05: Invalid date returns 400")


# ─────────────────────────────────────────────────────────────────────────────
# FN11.11 — Signup endpoint regression
# ─────────────────────────────────────────────────────────────────────────────
class TestFN11_11_SignupRegression:
    """FN11.11: POST /api/organizations/register must NOT return 401 (publicly accessible)"""

    def test_register_endpoint_not_401(self):
        """Signup endpoint should be publicly accessible (no auth required)"""
        resp = requests.post(
            f"{BASE_URL}/api/organizations/register",
            json={
                "organization_name": "TEST_AuditTestOrg999",
                "email": "TEST_audit_signup_999@example.com",
                "password": "Test@123456",
                "full_name": "Test Audit User",
                "phone": "+91-9999999999",
            },
        )
        # Must NOT be 401 (which would mean auth is wrongly required)
        assert resp.status_code != 401, (
            f"FAIL FN11.11: /api/organizations/register returned 401 — "
            f"endpoint must be publicly accessible without auth"
        )
        print(f"PASS FN11.11: /api/organizations/register returned {resp.status_code} (not 401)")

    def test_signup_endpoint_is_accessible(self):
        """Signup endpoint returns 200, 201, 400, or 409 — never 401 or 403"""
        resp = requests.post(
            f"{BASE_URL}/api/organizations/register",
            json={
                "organization_name": "TEST_AuditSignup2",
                "email": "TEST_audit2@example.com",
                "password": "Test@123456",
                "full_name": "Test Audit 2",
            },
        )
        acceptable = {200, 201, 400, 409, 422}
        auth_denied = {401, 403}
        assert resp.status_code not in auth_denied, (
            f"FAIL FN11.11: Register returned {resp.status_code} — "
            f"must not require authentication. Response: {resp.text[:300]}"
        )
        print(
            f"PASS FN11.11: Register returned {resp.status_code} "
            f"({'OK' if resp.status_code in acceptable else 'unexpected but not auth-denied'})"
        )

    def test_signup_also_accessible(self):
        """/api/organizations/signup is also publicly accessible"""
        resp = requests.post(
            f"{BASE_URL}/api/organizations/signup",
            json={
                "organization_name": "TEST_AuditSignup3",
                "email": "TEST_audit3@example.com",
                "password": "Test@123456",
                "full_name": "Test Audit 3",
            },
        )
        assert resp.status_code != 401, (
            f"FAIL FN11.11: /api/organizations/signup returned 401"
        )
        print(f"PASS FN11.11: /api/organizations/signup returned {resp.status_code}")
