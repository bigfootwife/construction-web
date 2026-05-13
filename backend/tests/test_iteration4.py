"""Iteration 4 tests: GET /projects/{id}, client documents CRUD, /upload extended MIME, TTL index."""
import os
import io
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


# ---------- GET /api/projects/{id} ----------
class TestProjectDetail:
    def test_get_project_by_id_returns_full_object(self):
        lst = requests.get(f"{API}/projects").json()
        assert lst, "no seeded projects"
        pid = lst[0]["project_id"]
        r = requests.get(f"{API}/projects/{pid}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["project_id"] == pid
        for k in ("title", "category", "location", "year", "description", "cover_image"):
            assert k in body and body[k] not in (None, "")

    def test_get_project_unknown_id_returns_404(self):
        r = requests.get(f"{API}/projects/prj_doesnotexist_xyz")
        assert r.status_code == 404


# ---------- /api/client/documents ----------
class TestClientDocuments:
    def test_list_documents_unauth_401(self):
        r = requests.get(f"{API}/client/documents")
        assert r.status_code == 401

    def test_list_documents_client_returns_only_own_4(self, client_session):
        r = client_session.get(f"{API}/client/documents")
        assert r.status_code == 200, r.text
        rows = r.json()
        # seeded: 2 test client projects * 2 sample docs = 4
        assert len(rows) >= 4
        # All docs must belong to one of the test client's cp_ids
        cps = client_session.get(f"{API}/client/projects").json()
        my_cps = {cp["cp_id"] for cp in cps}
        for d in rows:
            assert d["cp_id"] in my_cps, f"doc {d['doc_id']} cp={d['cp_id']} not in client's projects"

    def test_list_documents_client_other_cp_returns_403(self, admin_session, client_session):
        # Create an "other" client project (not assigned to test client)
        other_email = f"other_{uuid.uuid4().hex[:6]}@example.com"
        r = admin_session.post(f"{API}/client/projects", json={
            "client_email": other_email,
            "title": "TEST_OtherClientProj",
            "project_type": "Residential",
        })
        assert r.status_code == 200, r.text
        other_cp_id = r.json()["cp_id"]
        try:
            rr = client_session.get(f"{API}/client/documents", params={"cp_id": other_cp_id})
            assert rr.status_code == 403, f"expected 403 got {rr.status_code}: {rr.text}"
        finally:
            _mongo().client_projects.delete_one({"cp_id": other_cp_id})

    def test_list_documents_admin_returns_all(self, admin_session):
        r = admin_session.get(f"{API}/client/documents")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 4

    def test_create_document_admin_ok(self, admin_session, client_session):
        cps = client_session.get(f"{API}/client/projects").json()
        cp_id = cps[0]["cp_id"]
        title = f"TEST_Doc_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{API}/client/documents", json={
            "cp_id": cp_id, "title": title,
            "file_url": "https://example.com/test.pdf",
            "file_type": "application/pdf", "size": 1024,
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["title"] == title and body["cp_id"] == cp_id
        doc_id = body["doc_id"]
        # GET to verify persistence (admin sees all)
        listed = admin_session.get(f"{API}/client/documents").json()
        assert any(d["doc_id"] == doc_id for d in listed)
        # cleanup
        admin_session.delete(f"{API}/client/documents/{doc_id}")

    def test_create_document_client_403(self, client_session):
        cps = client_session.get(f"{API}/client/projects").json()
        cp_id = cps[0]["cp_id"]
        r = client_session.post(f"{API}/client/documents", json={
            "cp_id": cp_id, "title": "TEST_HackDoc",
            "file_url": "https://x.com/x.pdf",
        })
        assert r.status_code == 403

    def test_create_document_invalid_cp_id_404(self, admin_session):
        r = admin_session.post(f"{API}/client/documents", json={
            "cp_id": "cp_doesnotexist_xyz", "title": "TEST_X",
            "file_url": "https://x.com/x.pdf",
        })
        assert r.status_code == 404

    def test_delete_document_admin_ok(self, admin_session, client_session):
        cps = client_session.get(f"{API}/client/projects").json()
        cp_id = cps[0]["cp_id"]
        c = admin_session.post(f"{API}/client/documents", json={
            "cp_id": cp_id, "title": f"TEST_DelDoc_{uuid.uuid4().hex[:5]}",
            "file_url": "https://example.com/del.pdf",
        }).json()
        doc_id = c["doc_id"]
        r = admin_session.delete(f"{API}/client/documents/{doc_id}")
        assert r.status_code == 200
        # verify removed
        listed = admin_session.get(f"{API}/client/documents").json()
        assert not any(d["doc_id"] == doc_id for d in listed)

    def test_delete_document_client_403(self, client_session):
        # Use a seeded doc id
        rows = client_session.get(f"{API}/client/documents").json()
        assert rows
        r = client_session.delete(f"{API}/client/documents/{rows[0]['doc_id']}")
        assert r.status_code == 403


# ---------- /api/upload extended MIME ----------
class TestUploadExtendedMime:
    def test_upload_rejects_unknown_extension_400(self, admin_session):
        # exe is not in MIME_BY_EXT
        files = {"file": ("evil.exe", b"MZ\x90", "application/octet-stream")}
        r = admin_session.post(f"{API}/upload", files=files)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text}"

    def test_upload_accepts_pdf(self, admin_session):
        # Minimal pdf signature
        pdf_bytes = b"%PDF-1.4\n%TEST\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
        files = {"file": ("test_iter4.pdf", pdf_bytes, "application/pdf")}
        r = admin_session.post(f"{API}/upload", files=files)
        # Accept 200 (storage worked) or 503 (storage unavailable in test env), but NOT 400
        assert r.status_code in (200, 503), f"unexpected status {r.status_code}: {r.text}"
        if r.status_code == 200:
            assert "url" in r.json()

    def test_upload_accepts_docx(self, admin_session):
        files = {"file": ("test_iter4.docx", b"PK\x03\x04dummydocx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        r = admin_session.post(f"{API}/upload", files=files)
        assert r.status_code in (200, 503), f"unexpected status {r.status_code}: {r.text}"


# ---------- TTL index check ----------
class TestTTLIndex:
    def test_login_attempts_has_ttl_index_on_failed_at(self):
        idx = _mongo().login_attempts.index_information()
        # find an index keyed on failed_at with expireAfterSeconds=86400
        ttl_found = False
        for name, info in idx.items():
            keys = info.get("key", [])
            if any(k == "failed_at" for k, _ in keys) and info.get("expireAfterSeconds") == 86400:
                ttl_found = True
                break
        assert ttl_found, f"TTL index on failed_at with 86400s not found. Indexes: {idx}"

    def test_failed_at_stored_as_bson_datetime(self):
        _clear_login_attempts()
        email = f"ttltest_{uuid.uuid4().hex[:6]}@example.com"
        requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
        row = _mongo().login_attempts.find_one({"identifier": f"email:{email}"})
        assert row, "no failed_at row recorded"
        # pymongo deserializes BSON datetime to python datetime
        from datetime import datetime as _dt
        assert isinstance(row["failed_at"], _dt), f"failed_at type was {type(row['failed_at'])}"
        _clear_login_attempts()


# ---------- Regression: rate limiting still triggers ----------
class TestRateLimitRegression:
    def test_five_fails_then_429(self):
        _clear_login_attempts()
        email = f"regress_{uuid.uuid4().hex[:6]}@example.com"
        for _ in range(5):
            r = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
            assert r.status_code == 401
        r6 = requests.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
        assert r6.status_code == 429
        _clear_login_attempts()
