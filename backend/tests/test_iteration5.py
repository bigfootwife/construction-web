"""Iteration 5 tests: comments CRUD with access control + soft-delete of doc blob."""
import io
import os
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://build-hub-551.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@stonebridge.com", "password": "Admin@1234"}
CLIENT = {"email": "client@stonebridge.com", "password": "Client@1234"}


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


def _mongo():
    return MongoClient(MONGO_URL)[DB_NAME]


def _clear_login_attempts():
    if MONGO_URL and DB_NAME:
        _mongo().login_attempts.delete_many({})


@pytest.fixture(autouse=True, scope="module")
def _attempts_cleanup():
    _clear_login_attempts()
    yield
    _clear_login_attempts()


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=ADMIN)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def client_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=CLIENT)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def client_cp_ids(client_session):
    r = client_session.get(f"{API}/client/projects")
    assert r.status_code == 200
    cps = r.json()
    assert len(cps) >= 2, f"expected >=2 client_projects, got {len(cps)}"
    return [cp["cp_id"] for cp in cps]


@pytest.fixture(scope="module")
def other_cp_id(admin_session, client_cp_ids):
    """Create a foreign client_project that the test client does NOT own."""
    payload = {
        "client_email": f"foreign_{uuid.uuid4().hex[:6]}@example.com",
        "title": "TEST_Foreign Project",
        "project_type": "Residential",
        "progress": 0,
        "status": "Planning",
    }
    r = admin_session.post(f"{API}/client/projects", json=payload)
    assert r.status_code == 200, r.text
    cp_id = r.json()["cp_id"]
    yield cp_id
    # cleanup created cp + any comments on it
    if MONGO_URL and DB_NAME:
        db = _mongo()
        db.client_projects.delete_one({"cp_id": cp_id})
        db.comments.delete_many({"cp_id": cp_id})


# ============ COMMENTS LIST ============
class TestCommentsList:
    def test_unauth_401(self, client_cp_ids):
        r = requests.get(f"{API}/client/comments", params={"cp_id": client_cp_ids[0]})
        assert r.status_code == 401

    def test_client_can_list_own(self, client_session, client_cp_ids):
        r = client_session.get(f"{API}/client/comments", params={"cp_id": client_cp_ids[0]})
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # seeded welcome comment on first cp
        admin_seed = [c for c in data if c["author_role"] == "admin" and "Welcome" in c["body"]]
        assert len(admin_seed) >= 1, "expected seeded welcome comment"

    def test_client_other_cp_403(self, client_session, other_cp_id):
        r = client_session.get(f"{API}/client/comments", params={"cp_id": other_cp_id})
        assert r.status_code == 403

    def test_admin_can_list_any(self, admin_session, other_cp_id):
        r = admin_session.get(f"{API}/client/comments", params={"cp_id": other_cp_id})
        assert r.status_code == 200


# ============ COMMENTS CREATE ============
class TestCommentsCreate:
    def test_unauth_401(self, client_cp_ids):
        r = requests.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": "hi"})
        assert r.status_code == 401

    def test_client_post_on_own(self, client_session, client_cp_ids):
        body = f"TEST_client {uuid.uuid4().hex[:6]}"
        r = client_session.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": body})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["body"] == body
        assert data["author_role"] == "client"
        assert data["cp_id"] == client_cp_ids[0]
        assert data["comment_id"].startswith("cmt_")
        # GET-verify
        r2 = client_session.get(f"{API}/client/comments", params={"cp_id": client_cp_ids[0]})
        assert any(c["comment_id"] == data["comment_id"] for c in r2.json())
        # cleanup
        client_session.delete(f"{API}/client/comments/{data['comment_id']}")

    def test_client_post_on_other_403(self, client_session, other_cp_id):
        r = client_session.post(f"{API}/client/comments", json={"cp_id": other_cp_id, "body": "x"})
        assert r.status_code == 403

    def test_admin_post_on_any(self, admin_session, other_cp_id):
        r = admin_session.post(f"{API}/client/comments", json={"cp_id": other_cp_id, "body": "TEST_admin reply"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["author_role"] == "admin"
        admin_session.delete(f"{API}/client/comments/{data['comment_id']}")

    def test_empty_body_422(self, client_session, client_cp_ids):
        r = client_session.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": ""})
        assert r.status_code == 422


# ============ COMMENTS DELETE ============
class TestCommentsDelete:
    def test_admin_can_delete_any(self, admin_session, client_session, client_cp_ids):
        # client posts
        r = client_session.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": "TEST_to_delete_by_admin"})
        cmt = r.json()["comment_id"]
        # admin deletes
        d = admin_session.delete(f"{API}/client/comments/{cmt}")
        assert d.status_code == 200
        # verify gone
        rows = client_session.get(f"{API}/client/comments", params={"cp_id": client_cp_ids[0]}).json()
        assert not any(c["comment_id"] == cmt for c in rows)

    def test_client_can_delete_own(self, client_session, client_cp_ids):
        r = client_session.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": "TEST_mine"})
        cmt = r.json()["comment_id"]
        d = client_session.delete(f"{API}/client/comments/{cmt}")
        assert d.status_code == 200

    def test_client_cannot_delete_others(self, admin_session, client_session, client_cp_ids):
        # admin posts on client's cp
        r = admin_session.post(f"{API}/client/comments", json={"cp_id": client_cp_ids[0], "body": "TEST_admin_msg"})
        cmt = r.json()["comment_id"]
        # client tries to delete admin's
        d = client_session.delete(f"{API}/client/comments/{cmt}")
        assert d.status_code == 403
        # cleanup
        admin_session.delete(f"{API}/client/comments/{cmt}")

    def test_delete_unknown_404(self, admin_session):
        r = admin_session.delete(f"{API}/client/comments/cmt_doesnotexist")
        assert r.status_code == 404


# ============ SEED WELCOME COMMENT ============
class TestSeedWelcome:
    def test_seed_welcome_comment_exists(self):
        if not (MONGO_URL and DB_NAME):
            pytest.skip("no mongo env")
        db = _mongo()
        welcome = list(db.comments.find({"author_role": "admin", "body": {"$regex": "^Welcome"}}))
        assert len(welcome) >= 1


# ============ SOFT DELETE BLOB ON DOC DELETE ============
class TestDocDeleteSoftDeletesBlob:
    def test_doc_delete_marks_file_is_deleted_and_serve_404(self, admin_session, client_cp_ids):
        # 1. Upload PNG via /api/upload to get storage-backed file_url
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
        files = {"file": ("test_iter5.png", io.BytesIO(png), "image/png")}
        up = admin_session.post(f"{API}/upload", files=files)
        if up.status_code == 503:
            pytest.skip("storage transiently unavailable")
        assert up.status_code == 200, up.text
        file_url = up.json()["url"]
        assert "/api/files/" in file_url
        # Serve before delete -> 200
        serve_url = file_url if file_url.startswith("http") else f"{BASE_URL}{file_url}"
        serve_before = requests.get(serve_url, allow_redirects=False)
        assert serve_before.status_code in (200, 302, 307), f"pre-delete serve got {serve_before.status_code}"

        # 2. Attach as client document
        doc_payload = {
            "cp_id": client_cp_ids[0],
            "title": "TEST_blob_softdelete",
            "file_url": file_url,
            "file_type": "image/png",
            "size": len(png),
        }
        cd = admin_session.post(f"{API}/client/documents", json=doc_payload)
        assert cd.status_code == 200, cd.text
        doc_id = cd.json()["doc_id"]

        # 3. Delete the document
        dd = admin_session.delete(f"{API}/client/documents/{doc_id}")
        assert dd.status_code == 200

        # 4. files.is_deleted should be True
        if MONGO_URL and DB_NAME:
            path = file_url.split("/api/files/", 1)[1]
            f = _mongo().files.find_one({"storage_path": path})
            assert f is not None, "file row should still exist"
            assert f.get("is_deleted") is True
            assert f.get("deleted_at")

        # 5. GET /api/files/<path> now 404
        serve_after = requests.get(serve_url, allow_redirects=False)
        assert serve_after.status_code == 404, f"expected 404 after soft-delete, got {serve_after.status_code}"
