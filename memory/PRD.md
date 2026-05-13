# Stonebridge Construction — Product Requirements

## Original Problem Statement
> "Act as a senior full-stack web developer. Create a complete, production-ready website scaffold for a company specializing in building construction, residential renovations, and project management. Tech Stack: React (Frontend), java spring boot(Backend), MongoDB (Database), Tailwind CSS (Styling). Pages: Home (landing), Services (construction & renovation), Portfolio (portfolio), About, Contact (inquiry form), and Client Dashboard. Features: Clean, modern, and responsive design, image gallery for projects, form submission handling."

> Backend stack adjusted from Spring Boot → FastAPI (platform constraint).

## User Personas
- **Prospective Client** — browses portfolio, reads about services, submits inquiry.
- **Active Client** — logs in to track project progress, milestones, documents.
- **Studio Admin** — reviews incoming inquiries, manages portfolio projects, assigns client projects.

## Core Requirements (Static)
- 6 public pages: Home, Services, Portfolio, About, Contact, Login/Register.
- Authenticated Client Dashboard with project status tracking.
- Filterable image gallery with lightbox.
- Working inquiry form persisted to MongoDB.
- Premium architectural design (warm earthy tones, editorial typography).
- Responsive across mobile / tablet / desktop.

## Architecture
- **Frontend:** React + React Router + Framer Motion + Tailwind + Sonner toasts.
- **Backend:** FastAPI + Motor (MongoDB async) + PyJWT + bcrypt + Emergent Google OAuth.
- **DB Collections:** `users`, `sessions`, `projects`, `client_projects`, `inquiries`.
- **Auth:** JWT cookies (httpOnly, secure, samesite=none) + Bearer fallback + Emergent Google session_id flow.

## Implemented (2026-02-13)
- ✅ All 6 pages with editorial-grade design (Cabinet Grotesk / Manrope, terracotta + moss + sand palette).
- ✅ FastAPI backend with 11 endpoints (auth, projects, inquiries, client projects).
- ✅ Seeded data: admin user, test client, 6 portfolio projects, 2 client projects.
- ✅ JWT email/password auth + Emergent Google social login.
- ✅ Portfolio filterable gallery + animated lightbox (Framer Motion).
- ✅ Contact form with budget chip selector, project type, success state.
- ✅ Client dashboard with progress bars, milestones, stat cards.
- ✅ Admin view in dashboard (recent inquiries panel).
- ✅ 100% backend pytest coverage on critical endpoints, 95% frontend smoke pass.

## Prioritized Backlog

### P0 (next iteration)
- Email notification on inquiry submission via **Resend** (requires `RESEND_API_KEY`).
- Admin image upload UI for portfolio projects via **Emergent Object Storage**.

### P1
- Rate limiting / brute-force lockout on `/api/auth/login` (5 fails = 15min lockout).
- Switch `requests` → `httpx.AsyncClient` in `google-session` for async non-blocking.
- Suppress public-route 401 console noise from `/api/auth/me`.
- Documents/messages tab in client dashboard (currently stubbed counts).

### P2
- Refactor `server.py` (~500 lines) into modules (`auth.py`, `projects.py`, `inquiries.py`).
- Add `role='progressbar'` + ARIA attributes for dashboard accessibility.
- SEO meta tags + Open Graph images per page.
- Project detail pages (currently lightbox only).

## Test Credentials
See `/app/memory/test_credentials.md`.
