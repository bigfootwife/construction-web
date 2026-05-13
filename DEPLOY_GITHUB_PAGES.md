# Stonebridge — Static Site Mode (GitHub Pages Ready)

This project ships with a **dual-mode** architecture so the same React codebase can deploy two ways:

| Mode | What it does | Where it deploys |
|---|---|---|
| **Static** (`REACT_APP_STATIC_MODE=true`) | View-only marketing site. Portfolio loaded from local JS file. Inquiry form opens user's email app via `mailto:`. No backend, no DB. | **GitHub Pages**, Netlify, Vercel, S3, anywhere static. |
| **Full-stack** (`REACT_APP_STATIC_MODE=false`) | All features on: auth, client dashboard, admin uploads, comments, email notifications, MongoDB persistence. | Emergent native deploy, Render, Railway, etc. |

You can flip between the two by changing one env var. Backend code stays in place.

---

## Deploy to GitHub Pages — Step by Step

### 1. Set the GitHub Pages URL

In `/app/frontend/package.json`, add (or update) the `homepage` field. Replace `<username>` and `<repo>` with your GitHub username and repository name:

```json
{
  "homepage": "https://<username>.github.io/<repo>",
  "name": "frontend",
  ...
}
```

> Example: `https://davidgumaraol.github.io/stonebridge`

### 2. Confirm the static-mode env vars

`/app/frontend/.env` already contains:

```
REACT_APP_STATIC_MODE=true
REACT_APP_STUDIO_EMAIL=davidgumaraol@gmail.com
REACT_APP_SITE_NAME=Stonebridge Construction Co.
REACT_APP_OG_IMAGE_URL=https://...
```

Change `REACT_APP_STUDIO_EMAIL` to the address you want inquiry-form submissions sent to (the form opens the user's mail client with this address pre-filled).

### 3. Push the project to GitHub

In Emergent: click **Save to GitHub** in the top-right UI to push your code to a fresh repo. Or, locally:

```bash
cd /app
git init -b main
git remote add origin https://github.com/<username>/<repo>.git
git add .
git commit -m "Initial Stonebridge build (static mode)"
git push -u origin main
```

### 4. Build & deploy to GitHub Pages

```bash
cd frontend
yarn install
yarn deploy
```

The `yarn deploy` script (already wired up in `package.json`) runs `yarn build` and then pushes the `build/` folder to the **`gh-pages` branch** of your repo using the `gh-pages` package.

### 5. Enable GitHub Pages in repo settings

1. Go to your repo on GitHub → **Settings** → **Pages**.
2. Under "Source", choose **Deploy from a branch**.
3. Set branch to **`gh-pages`** and folder to **`/ (root)`**.
4. Save. Wait ~1 minute. Your site is live at the `homepage` URL.

---

## Why `HashRouter`?

GitHub Pages doesn't support server-side SPA routing (deep links like `/portfolio/abc` return 404). To work around this, the app uses **`HashRouter`** when `REACT_APP_STATIC_MODE=true`, so deep links look like:

```
https://<username>.github.io/<repo>/#/portfolio/prj_static_maple_ridge
```

Visually identical UX, no routing surprises. When you switch back to full-stack mode, the app reverts to clean `BrowserRouter` URLs automatically.

---

## Switching Back to Full Backend

When you decide to re-enable the backend (auth, dashboard, admin, comments, email notifications):

1. In `/app/frontend/.env`, set:
   ```
   REACT_APP_STATIC_MODE=false
   REACT_APP_BACKEND_URL=https://your-backend-host.example.com
   ```
2. Deploy the FastAPI backend (in `/app/backend/`) to:
   - **Emergent native deploy** (recommended — handles everything, 50 credits/month), OR
   - Render / Railway / Fly.io with MongoDB Atlas as the database.
3. Re-deploy the frontend (with the new env, to GitHub Pages or your other host).

Every page, route, component, and API endpoint is preserved in source — only the env flag changes.

---

## What's Live in Static Mode

✅ Home (with featured projects from local data)
✅ Services
✅ Portfolio (filterable gallery + lightbox + detail pages)
✅ About
✅ Contact (form opens the user's email client pre-filled — no backend needed)
✅ All design, animations, typography, SEO meta tags

## What's Hidden in Static Mode

❌ Client Login / Register
❌ Client Dashboard
❌ Admin Console
❌ Real-time comments
❌ Document upload / management
❌ Auto inquiry email via Resend

These pages and their code stay in `/app/frontend/src/pages/{Login,Register,Dashboard,Admin,AuthCallback}.jsx` for the future flip.

---

## Files Changed for Static Mode

- `src/data/staticProjects.js` — local seed (6 projects, no backend dependency)
- `src/lib/dataLayer.js` — abstracts data access; routes through API or local data based on the flag
- `src/App.js` — conditional routes; `HashRouter` in static mode
- `src/components/Header.jsx` — hides "Client Login"; shows "Start a Project" instead
- `src/pages/{Home,Portfolio,ProjectDetail,Contact}.jsx` — go through `dataLayer` instead of `api`
- `src/context/AuthContext.jsx` — skips `/me` ping in static mode
- `package.json` — `homepage` field + `gh-pages` dev dep + `deploy` script
