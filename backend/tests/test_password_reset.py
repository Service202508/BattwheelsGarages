"""
Password Reset — All 3 Flows Tests
=====================================
Flow 1: Admin resets employee password
Flow 2: Self-service password change
Flow 3: Forgot password via email + token reset
"""
import os
import pytest
import httpx
import asyncio
import hashlib

API_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
AUTH = f"{API_URL}/api/auth"
V1 = f"{API_URL}/api/v1"

# Test credentials
ADMIN_EMAIL = "admin@battwheels.in"
ADMIN_PASSWORD = "Admin@12345"

STRONG_PASSWORD = "NewSecure@123"

def run_async(coro):
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return loop.run_until_complete(coro)


async def admin_login():
    """Login with retry for rate limiting."""
    import time
    for attempt in range(3):
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{AUTH}/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
            if resp.status_code == 429:
                await asyncio.sleep(2)
                continue
            data = resp.json()
            token = data.get("token", "")
            if token:
                return token
    raise RuntimeError("Failed to login after retries")


async def get_org_id(token):
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{AUTH}/me", headers={"Authorization": f"Bearer {token}"})
        data = resp.json()
        orgs = data.get("organizations", [])
        return orgs[0]["organization_id"] if orgs else ""


# ─────────────────────────────────────────────────────
# Flow 2: Self-service password change
# ─────────────────────────────────────────────────────
class TestSelfServicePasswordChange:

    def test_change_password_wrong_current(self):
        """POST change-password with wrong current → 401"""
        async def _test():
            token = await admin_login()
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/change-password",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"current_password": "WrongPassword@1", "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
                assert "incorrect" in resp.json()["detail"].lower()
        run_async(_test())

    def test_change_password_success(self):
        """POST change-password with correct current → success, then change back"""
        async def _test():
            token = await admin_login()
            async with httpx.AsyncClient(timeout=15) as client:
                # Change to temp password
                resp = await client.post(
                    f"{AUTH}/change-password",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"current_password": ADMIN_PASSWORD, "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 200, f"Change failed: {resp.text}"
                assert "success" in resp.json()["message"].lower()

                # Login with new password (with retry for rate limit)
                await asyncio.sleep(1)
                resp2 = None
                for _ in range(3):
                    resp2 = await client.post(f"{AUTH}/login", json={"email": ADMIN_EMAIL, "password": STRONG_PASSWORD})
                    if resp2.status_code != 429:
                        break
                    await asyncio.sleep(2)
                assert resp2.status_code == 200, f"Login with new password failed: {resp2.text}"
                new_token = resp2.json()["token"]

                # Change back
                await asyncio.sleep(1)
                resp3 = await client.post(
                    f"{AUTH}/change-password",
                    headers={"Authorization": f"Bearer {new_token}"},
                    json={"current_password": STRONG_PASSWORD, "new_password": ADMIN_PASSWORD},
                )
                assert resp3.status_code == 200, f"Change back failed: {resp3.text}"
        run_async(_test())

    def test_change_password_weak_password(self):
        """POST change-password with weak new password → 422"""
        async def _test():
            token = await admin_login()
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/change-password",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"current_password": ADMIN_PASSWORD, "new_password": "weak"},
                )
                assert resp.status_code == 422
        run_async(_test())


# ─────────────────────────────────────────────────────
# Flow 3: Forgot password via email
# ─────────────────────────────────────────────────────
class TestForgotPassword:

    def test_forgot_password_valid_email(self):
        """POST forgot-password with valid email → 200, token created"""
        async def _test():
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{AUTH}/forgot-password", json={"email": ADMIN_EMAIL})
                assert resp.status_code == 200
                assert "reset link" in resp.json()["message"].lower()

            # Verify token in DB (stored as hash)
            from motor.motor_asyncio import AsyncIOMotorClient
            mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db_client = mongo[os.environ.get("DB_NAME", "battwheels")]
            doc = await db_client.password_reset_tokens.find_one(
                {"email": ADMIN_EMAIL, "used": False},
                sort=[("created_at", -1)]
            )
            assert doc is not None, "Token not created in DB"
            assert "token_hash" in doc, "Token not stored as hash"
            assert len(doc["token_hash"]) == 64, f"Hash length wrong: {len(doc['token_hash'])}"
            # Cleanup
            await db_client.password_reset_tokens.delete_many({"email": ADMIN_EMAIL})
        run_async(_test())

    def test_forgot_password_unknown_email(self):
        """POST forgot-password with unknown email → 200, no info leak"""
        async def _test():
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{AUTH}/forgot-password", json={"email": "nonexistent@nowhere.com"})
                assert resp.status_code == 200
                assert "reset link" in resp.json()["message"].lower()

            # Verify no token created
            from motor.motor_asyncio import AsyncIOMotorClient
            mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db_client = mongo[os.environ.get("DB_NAME", "battwheels")]
            doc = await db_client.password_reset_tokens.find_one({"email": "nonexistent@nowhere.com"})
            assert doc is None, "Token created for non-existent email — info leak!"
        run_async(_test())

    def test_reset_password_invalid_token(self):
        """POST reset-password with invalid token → 400"""
        async def _test():
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/reset-password",
                    json={"token": "totally_invalid_token", "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 400
                assert "invalid" in resp.json()["detail"].lower() or "expired" in resp.json()["detail"].lower()
        run_async(_test())

    def test_reset_password_valid_token(self):
        """POST reset-password with valid token → password updated, token used"""
        async def _test():
            import secrets
            from motor.motor_asyncio import AsyncIOMotorClient
            from datetime import datetime, timezone, timedelta

            mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db_client = mongo[os.environ.get("DB_NAME", "battwheels")]

            # Find admin user_id
            admin_user = await db_client.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "user_id": 1})

            # Insert a valid token directly
            raw_token = secrets.token_urlsafe(48)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
            await db_client.password_reset_tokens.insert_one({
                "user_id": admin_user["user_id"],
                "email": ADMIN_EMAIL,
                "token_hash": token_hash,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used": False,
            })

            # Reset password using the token
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/reset-password",
                    json={"token": raw_token, "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 200, f"Reset failed: {resp.text}"

                # Login with new password (with retry for rate limit)
                await asyncio.sleep(1)
                resp2 = None
                for _ in range(3):
                    resp2 = await client.post(f"{AUTH}/login", json={"email": ADMIN_EMAIL, "password": STRONG_PASSWORD})
                    if resp2.status_code != 429:
                        break
                    await asyncio.sleep(2)
                assert resp2.status_code == 200, f"Login with new password failed: {resp2.status_code}"

                # Change password back
                new_token = resp2.json()["token"]
                await asyncio.sleep(1)
                resp3 = await client.post(
                    f"{AUTH}/change-password",
                    headers={"Authorization": f"Bearer {new_token}"},
                    json={"current_password": STRONG_PASSWORD, "new_password": ADMIN_PASSWORD},
                )
                assert resp3.status_code == 200, f"Change back failed: {resp3.text}"

            # Verify token is marked as used
            used_doc = await db_client.password_reset_tokens.find_one({"token_hash": token_hash})
            assert used_doc["used"] is True, "Token not marked as used"
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
        run_async(_test())

    def test_reset_password_used_token(self):
        """POST reset-password with already-used token → 400"""
        async def _test():
            import secrets
            from motor.motor_asyncio import AsyncIOMotorClient
            from datetime import datetime, timezone, timedelta

            mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db_client = mongo[os.environ.get("DB_NAME", "battwheels")]
            admin_user = await db_client.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "user_id": 1})

            raw_token = secrets.token_urlsafe(48)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
            await db_client.password_reset_tokens.insert_one({
                "user_id": admin_user["user_id"],
                "email": ADMIN_EMAIL,
                "token_hash": token_hash,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used": True,  # Already used
            })

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/reset-password",
                    json={"token": raw_token, "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 400
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
        run_async(_test())

    def test_reset_password_expired_token(self):
        """POST reset-password with expired token → 400"""
        async def _test():
            import secrets
            from motor.motor_asyncio import AsyncIOMotorClient
            from datetime import datetime, timezone, timedelta

            mongo = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
            db_client = mongo[os.environ.get("DB_NAME", "battwheels")]
            admin_user = await db_client.users.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "user_id": 1})

            raw_token = secrets.token_urlsafe(48)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
            await db_client.password_reset_tokens.insert_one({
                "user_id": admin_user["user_id"],
                "email": ADMIN_EMAIL,
                "token_hash": token_hash,
                "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used": False,
            })

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{AUTH}/reset-password",
                    json={"token": raw_token, "new_password": STRONG_PASSWORD},
                )
                assert resp.status_code == 400
            await db_client.password_reset_tokens.delete_many({"user_id": admin_user["user_id"]})
        run_async(_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
