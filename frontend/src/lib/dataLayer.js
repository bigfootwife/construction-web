// Data layer — abstracts data access so the UI works in both modes:
//   STATIC_MODE=true  → reads from local seed (GitHub Pages, no backend)
//   STATIC_MODE=false → uses the FastAPI backend (full app)
//
// Flip REACT_APP_STATIC_MODE in /app/frontend/.env to switch.

import api from "./api";
import { STATIC_PROJECTS } from "../data/staticProjects";

export const STATIC_MODE = process.env.REACT_APP_STATIC_MODE === "true";
export const STUDIO_EMAIL = process.env.REACT_APP_STUDIO_EMAIL || "hello@stonebridge.com";

export async function listProjects({ category, featured } = {}) {
  if (STATIC_MODE) {
    let rows = [...STATIC_PROJECTS];
    if (category && category !== "all") rows = rows.filter((p) => p.category === category);
    if (typeof featured === "boolean") rows = rows.filter((p) => p.featured === featured);
    return rows.sort((a, b) => b.year - a.year);
  }
  const params = new URLSearchParams();
  if (category && category !== "all") params.set("category", category);
  if (typeof featured === "boolean") params.set("featured", String(featured));
  const qs = params.toString();
  const { data } = await api.get(`/projects${qs ? `?${qs}` : ""}`);
  return data;
}

export async function getProject(id) {
  if (STATIC_MODE) {
    return STATIC_PROJECTS.find((p) => p.project_id === id) || null;
  }
  try {
    const { data } = await api.get(`/projects/${id}`);
    return data;
  } catch (err) {
    if (err?.response?.status === 404) return null;
    throw err;
  }
}

export async function submitInquiry(payload) {
  if (STATIC_MODE) {
    // No backend — open the user's mail client with a pre-filled message.
    const subject = `Project Inquiry · ${payload.project_type}`;
    const lines = [
      `Name: ${payload.name}`,
      `Email: ${payload.email}`,
      payload.phone ? `Phone: ${payload.phone}` : null,
      `Project Type: ${payload.project_type}`,
      payload.budget ? `Budget: ${payload.budget}` : null,
      "",
      payload.message,
    ].filter(Boolean);
    const body = lines.join("\n");
    window.location.href = `mailto:${STUDIO_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    return { ok: true, mode: "mailto" };
  }
  const { data } = await api.post("/inquiries", payload);
  return { ok: true, mode: "api", data };
}
