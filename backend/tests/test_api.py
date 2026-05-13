import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://build-hub-551.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@stonebridge.com", "password": "Admin@1234"}
CLIENT = {"email": "client@stonebridge.com", "password": "Client@1234"}


# ----- Projects (public) -----
class TestProjects:
    def test_list_all(self):
        r = requests.get(f"{API}/projects")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 6, f"expected >=6 seeded projects, got {len(data)}"
        for p in data:
            assert "project_id" in p and "title" in p and "category" in p

    def test_filter_residential(self):
        r = requests.get(f"{API}/projects", params={"category": "residential"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert all(p["category"] == "residential" for p in data)

    def test_filter_featured(self):
        r = requests.get(f"{API}/projects", params={"featured": "true"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert all(p["featured"] is True for p in data)


# ----- Inquiries (public POST, admin GET) -----
class TestInquiries:
    def test_create_inquiry_public(self):
        payload = {
            "name": "TEST_Inquiry User",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-0100",
            "project_type": "residential",
            "budget": "$500k-$1M",
            "message": "TEST inquiry from automation",
        }
        r = requests.post(f"{API}/inquiries", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "new"
        assert data["name"] == payload["name"]
        assert "inquiry_id" in data


# ----- Auth -----
class TestAuth:
    def test_admin_login(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json=ADMIN)
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "admin"
        assert "access_token" in s.cookies.get_dict()
        # me
        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 200
        assert r2.json()["email"] == ADMIN["email"]

    def test_client_login(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json=CLIENT)
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "client"

    def test_invalid_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "wrong"})
        assert r.status_code == 401

    def test_register_new_user(self):
        email = f"test_reg_{uuid.uuid4().hex[:8]}@example.com"
        s = requests.Session()
        r = s.post(f"{API}/auth/register", json={"name": "TEST New", "email": email, "password": "Pass@1234"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["email"] == email
        assert body["role"] == "client"
        assert "access_token" in s.cookies.get_dict()
        # duplicate
        r2 = requests.post(f"{API}/auth/register", json={"name": "Dup", "email": email, "password": "Pass@1234"})
        assert r2.status_code == 400

    def test_logout_clears_cookie(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json=ADMIN)
        assert r.status_code == 200
        r2 = s.post(f"{API}/auth/logout")
        assert r2.status_code == 200
        # access_token cookie should be cleared
        assert not s.cookies.get("access_token")
        r3 = s.get(f"{API}/auth/me")
        assert r3.status_code == 401


# ----- Role-based access -----
class TestAccess:
    def test_inquiries_requires_admin(self):
        # No auth
        r = requests.get(f"{API}/inquiries")
        assert r.status_code == 401
        # Client - 403
        cs = requests.Session()
        cs.post(f"{API}/auth/login", json=CLIENT)
        r2 = cs.get(f"{API}/inquiries")
        assert r2.status_code == 403
        # Admin - 200
        admins = requests.Session()
        admins.post(f"{API}/auth/login", json=ADMIN)
        r3 = admins.get(f"{API}/inquiries")
        assert r3.status_code == 200
        assert isinstance(r3.json(), list)

    def test_client_projects_for_test_client(self):
        s = requests.Session()
        s.post(f"{API}/auth/login", json=CLIENT)
        r = s.get(f"{API}/client/projects")
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data) == 2, f"expected 2 projects for test client, got {len(data)}"
        for cp in data:
            assert cp["client_email"] == CLIENT["email"]
            assert "progress" in cp

    def test_google_session_invalid(self):
        r = requests.post(f"{API}/auth/google-session", json={"session_id": "invalid_xyz"})
        assert r.status_code in (401, 500)
