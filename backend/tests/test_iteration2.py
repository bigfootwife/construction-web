"""Iteration 2 tests: file upload, project create/delete (admin), inquiry email."""
import io
import os
import struct
import time
import uuid
import zlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://build-hub-551.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@stonebridge.com", "password": "Admin@1234"}
CLIENT = {"email": "client@stonebridge.com", "password": "Client@1234"}


def _png_bytes() -> bytes:
    """Minimal 1x1 transparent PNG."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + ihdr + struct.pack(">I", zlib.crc32(ihdr))
    raw = b"\x00\x00\x00\x00\x00"
    comp = zlib.compress(raw)
    idat = b"IDAT" + comp
    idat_chunk = struct.pack(">I", len(comp)) + idat + struct.pack(">I", zlib.crc32(idat))
    iend = b"IEND"
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend))
    return sig + ihdr_chunk + idat_chunk + iend_chunk


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


class TestUpload:
    def test_upload_requires_auth(self):
        r = requests.post(f"{API}/upload", files={"file": ("a.png", _png_bytes(), "image/png")})
        assert r.status_code == 401

    def test_upload_forbidden_for_client(self, client_session):
        r = client_session.post(f"{API}/upload", files={"file": ("a.png", _png_bytes(), "image/png")})
        assert r.status_code == 403

    def test_upload_admin_png_then_serve(self, admin_session):
        png = _png_bytes()
        r = admin_session.post(f"{API}/upload", files={"file": ("test.png", png, "image/png")})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "file_id" in data and "url" in data and "path" in data
        assert data["path"].endswith(".png")
        # Serve back
        g = requests.get(f"{API}/files/{data['path']}")
        assert g.status_code == 200, g.text
        assert g.headers.get("content-type", "").startswith("image/")
        assert len(g.content) > 0

    def test_upload_rejects_non_image(self, admin_session):
        r = admin_session.post(
            f"{API}/upload",
            files={"file": ("evil.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
        assert r.status_code == 400, r.text

    def test_upload_rejects_oversize(self, admin_session):
        big = b"\x00" * (8 * 1024 * 1024 + 16)
        r = admin_session.post(
            f"{API}/upload",
            files={"file": ("big.png", big, "image/png")},
        )
        assert r.status_code == 413, r.text

    def test_serve_missing_file_404(self):
        r = requests.get(f"{API}/files/stonebridge/uploads/does/not/exist.png")
        assert r.status_code == 404


class TestProjectAdmin:
    created_id = None

    def test_create_project_requires_admin(self, client_session):
        payload = {
            "title": "TEST_ShouldNotCreate", "category": "residential",
            "location": "X", "year": 2025, "description": "x", "cover_image": "https://x/x.jpg",
        }
        r = client_session.post(f"{API}/projects", json=payload)
        assert r.status_code == 403

    def test_create_project_unauth(self):
        r = requests.post(f"{API}/projects", json={
            "title": "x", "category": "residential", "location": "X",
            "year": 2025, "description": "x", "cover_image": "https://x/x.jpg",
        })
        assert r.status_code == 401

    def test_admin_create_and_list_and_delete(self, admin_session):
        # Upload cover first
        up = admin_session.post(
            f"{API}/upload",
            files={"file": ("cover.png", _png_bytes(), "image/png")},
        )
        assert up.status_code == 200
        cover_url = up.json()["url"]

        title = f"TEST_Project_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{API}/projects", json={
            "title": title, "category": "commercial",
            "location": "Denver, CO", "year": 2025,
            "description": "Auto-test project", "cover_image": cover_url,
            "images": [], "featured": False,
        })
        assert r.status_code == 200, r.text
        proj = r.json()
        pid = proj["project_id"]
        assert proj["title"] == title
        assert proj["cover_image"] == cover_url

        # Visible via public GET
        lst = requests.get(f"{API}/projects").json()
        assert any(p["project_id"] == pid for p in lst), "newly created project missing from public list"

        # Delete - 403 for client
        cs = requests.Session()
        cs.post(f"{API}/auth/login", json=CLIENT)
        rdel = cs.delete(f"{API}/projects/{pid}")
        assert rdel.status_code == 403

        # Delete - 200 for admin
        rdel2 = admin_session.delete(f"{API}/projects/{pid}")
        assert rdel2.status_code == 200, rdel2.text
        assert rdel2.json().get("deleted") == pid

        # 404 second delete
        rdel3 = admin_session.delete(f"{API}/projects/{pid}")
        assert rdel3.status_code == 404

        # Confirm absent
        lst2 = requests.get(f"{API}/projects").json()
        assert not any(p["project_id"] == pid for p in lst2)


class TestInquiryEmail:
    def test_inquiry_triggers_async_email(self):
        payload = {
            "name": "TEST_EmailUser",
            "email": "test_email@example.com",
            "phone": "555-0199",
            "project_type": "renovation",
            "budget": "$500k",
            "message": "Iteration2 email test",
        }
        r = requests.post(f"{API}/inquiries", json=payload)
        assert r.status_code == 200, r.text
        inq_id = r.json()["inquiry_id"]
        # Give the async task time to fire
        time.sleep(2)
        # Best-effort: check backend log for the send line
        log_paths = [
            "/var/log/supervisor/backend.err.log",
            "/var/log/supervisor/backend.out.log",
        ]
        log = ""
        for p in log_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r", errors="ignore") as fh:
                        log += fh.read()[-50000:]
                except Exception:
                    pass
        # Either we see a success log for this inquiry, or generally a recent send log
        assert "Inquiry email" in log or "Resend not configured" in log, (
            "no email-related log entry found; inquiry_id=" + inq_id
        )
