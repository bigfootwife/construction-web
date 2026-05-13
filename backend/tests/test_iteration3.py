"""Iteration 3 tests: login rate limiting + PATCH /api/projects/{id} admin update."""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://build-hub-551.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@stonebridge.com", "password": "Admin@1234"}
CLIENT = {"email": "client@stonebridge.com", "password": "Client@1234"}

# Pull Mongo connection from backend/.env (same DB the server uses)
def _load_backend_env():
    env = {}
    p = "/app/backend/.env"
    if os.path.exists(p):
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

_BENV = _load_backend_env()
MONGO_URL = _BENV.get("MONGO_URL") or os.environ.get("MONGO_URL")
DB_NAME = _BENV.get("DB_NAME") or os.environ.get("DB_NAME")


def _clear_login_attempts():
    if MONGO_URL and DB_NAME:
        c = MongoClient(MONGO_URL)
        c[DB_NAME].login_attempts.delete_many({})
        c.close()


@pytest.fixture(autouse=True, scope="module")
def _attempts_cleanup_each_module():
    _clear_login_attempts()
    yield
    _clear_login_attempts()


@pytest.fixture(scope="module")
def admin_session():
    _clear_login_attempts()
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def client_session():
    _clear_login_attempts()
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=CLIENT)
    assert r.status_code == 200, r.text
    return s


# ---------- Rate limiting ----------
class TestRateLimit:
    def _bad_email(self):
        return f"ratelimit_{uuid.uuid4().hex[:8]}@example.com"

    def test_five_fails_then_locked(self):
        _clear_login_attempts()
        email = self._bad_email()
        # 5 failures -> all 401
        for i in range(5):
            r = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
            assert r.status_code == 401, f"attempt {i+1} expected 401, got {r.status_code}: {r.text}"
        # 6th -> 429
        r6 = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
        assert r6.status_code == 429, f"expected 429 lockout, got {r6.status_code}: {r6.text}"

    def test_lockout_scoped_per_identifier(self):
        """A locked-out victim email must NOT prevent a separate user from logging in."""
        _clear_login_attempts()
        victim = self._bad_email()
        for _ in range(5):
            requests.post(f"{API}/auth/login", json={"email": victim, "password": "wrong"})
        # Confirm victim is locked
        rv = requests.post(f"{API}/auth/login", json={"email": victim, "password": "wrong"})
        assert rv.status_code == 429
        # Admin must still be able to log in
        s = requests.Session()
        ra = s.post(f"{API}/auth/login", json=ADMIN)
        assert ra.status_code == 200, ra.text

    def test_successful_login_clears_attempts(self):
        _clear_login_attempts()
        # 4 fails for admin (under threshold)
        for _ in range(4):
            r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "wrong"})
            assert r.status_code == 401
        # Successful login should clear counters
        s = requests.Session()
        ok = s.post(f"{API}/auth/login", json=ADMIN)
        assert ok.status_code == 200
        # Now 5 fresh fails must again return 401 (not 429)
        for i in range(5):
            r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "wrong"})
            assert r.status_code == 401, f"after-success attempt {i+1} returned {r.status_code}"

    def test_email_only_identifier_catches_distributed_attack(self):
        """Even if attacker rotates X-Forwarded-For, email-only identifier should lock."""
        _clear_login_attempts()
        email = self._bad_email()
        # 5 attempts each with a different X-Forwarded-For IP
        for i in range(5):
            r = requests.post(
                f"{API}/auth/login",
                json={"email": email, "password": "wrong"},
                headers={"X-Forwarded-For": f"203.0.113.{i+1}"},
            )
            assert r.status_code == 401
        # 6th from yet another IP -> should still hit email-only lockout
        r6 = requests.post(
            f"{API}/auth/login",
            json={"email": email, "password": "wrong"},
            headers={"X-Forwarded-For": "203.0.113.99"},
        )
        assert r6.status_code == 429, f"distributed attack not blocked: {r6.status_code} {r6.text}"


# ---------- PATCH /api/projects/{id} ----------
class TestProjectPatch:
    @pytest.fixture
    def created_project(self, admin_session):
        # Use any existing seeded cover URL to avoid storage dependency
        seed = requests.get(f"{API}/projects").json()
        assert seed, "no seeded projects"
        cover = seed[0]["cover_image"]
        title = f"TEST_Patch_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{API}/projects", json={
            "title": title, "category": "residential",
            "location": "Test City", "year": 2025,
            "description": "Initial description",
            "cover_image": cover, "images": [], "featured": False,
        })
        assert r.status_code == 200, r.text
        pid = r.json()["project_id"]
        yield r.json()
        # cleanup
        admin_session.delete(f"{API}/projects/{pid}")

    def test_patch_as_admin_updates_only_provided_fields(self, admin_session, created_project):
        pid = created_project["project_id"]
        original_cover = created_project["cover_image"]
        new_title = f"TEST_PatchedTitle_{uuid.uuid4().hex[:5]}"
        r = admin_session.patch(f"{API}/projects/{pid}", json={
            "title": new_title,
            "description": "Updated description",
            "featured": True,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        # provided fields updated
        assert body["title"] == new_title
        assert body["description"] == "Updated description"
        assert body["featured"] == True
        # untouched fields preserved
        assert body["cover_image"] == original_cover
        assert body["category"] == created_project["category"]
        assert body["location"] == created_project["location"]
        assert body["year"] == created_project["year"]
        assert body["project_id"] == pid

        # Verify persistence via GET
        lst = requests.get(f"{API}/projects").json()
        match = [p for p in lst if p["project_id"] == pid]
        assert match and match[0]["title"] == new_title
        assert match[0]["featured"] == True

    def test_patch_forbidden_for_client(self, client_session, created_project):
        pid = created_project["project_id"]
        r = client_session.patch(f"{API}/projects/{pid}", json={"title": "TEST_HackedTitle"})
        assert r.status_code == 403

    def test_patch_unauth(self, created_project):
        r = requests.patch(f"{API}/projects/{created_project['project_id']}", json={"title": "x"})
        assert r.status_code == 401

    def test_patch_nonexistent_returns_404(self, admin_session):
        r = admin_session.patch(f"{API}/projects/prj_doesnotexist123", json={"title": "ghost"})
        assert r.status_code == 404

    def test_patch_empty_body_returns_400(self, admin_session, created_project):
        pid = created_project["project_id"]
        r = admin_session.patch(f"{API}/projects/{pid}", json={})
        assert r.status_code == 400
