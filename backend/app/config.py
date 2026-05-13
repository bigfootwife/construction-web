"""Configuration loaded from environment."""
import os

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@stonebridge.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@1234")
TEST_CLIENT_EMAIL = os.environ.get("TEST_CLIENT_EMAIL", "client@stonebridge.com")
TEST_CLIENT_PASSWORD = os.environ.get("TEST_CLIENT_PASSWORD", "Client@1234")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
INQUIRY_NOTIFICATION_EMAIL = os.environ.get("INQUIRY_NOTIFICATION_EMAIL")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = os.environ.get("APP_NAME", "stonebridge")
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15
LOGIN_ATTEMPT_TTL_SECONDS = 24 * 3600

MIME_BY_EXT = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "dwg": "image/vnd.dwg",
    "txt": "text/plain",
}
