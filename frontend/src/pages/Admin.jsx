import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Upload, Trash2, Plus, X, Image as ImageIcon, ArrowLeft, Pencil } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";

const CATEGORIES = ["residential", "commercial", "renovation"];
const EMPTY_FORM = {
  title: "", category: "residential", location: "", year: new Date().getFullYear(),
  description: "", cover_image: "", images: [], featured: false,
};

export default function Admin() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [inquiries, setInquiries] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const fileRef = useRef(null);
  const galleryRef = useRef(null);

  useEffect(() => {
    if (user && user.role !== "admin") {
      navigate("/dashboard");
      return;
    }
    refresh();
  }, [user, navigate]);

  const refresh = () => {
    api.get("/projects").then(({ data }) => setProjects(data)).catch(() => {});
    api.get("/inquiries").then(({ data }) => setInquiries(data)).catch(() => {});
  };

  const uploadFile = async (file) => {
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await api.post("/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data.url;
  };

  const onCoverPick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      const url = await uploadFile(file);
      setForm((f) => ({ ...f, cover_image: url }));
      toast.success("Cover image uploaded.");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const onGalleryPick = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setLoading(true);
    try {
      const urls = await Promise.all(files.map(uploadFile));
      setForm((f) => ({ ...f, images: [...f.images, ...urls] }));
      toast.success(`${urls.length} image(s) uploaded.`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const removeGalleryImg = (idx) =>
    setForm((f) => ({ ...f, images: f.images.filter((_, i) => i !== idx) }));

  const createProject = async (e) => {
    e.preventDefault();
    if (!form.cover_image) {
      toast.error("Please upload a cover image.");
      return;
    }
    setLoading(true);
    try {
      const payload = { ...form, year: Number(form.year) };
      if (editingId) {
        await api.patch(`/projects/${editingId}`, payload);
        toast.success(`Project "${form.title}" updated.`);
      } else {
        await api.post("/projects", payload);
        toast.success(`Project "${form.title}" created.`);
      }
      resetForm();
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not save project.");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setShowForm(false);
  };

  const startEdit = (project) => {
    setEditingId(project.project_id);
    setForm({
      title: project.title,
      category: project.category,
      location: project.location,
      year: project.year,
      description: project.description,
      cover_image: project.cover_image,
      images: project.images || [],
      featured: project.featured,
    });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const deleteProject = async (id, title) => {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/projects/${id}`);
      toast.success("Project deleted.");
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed.");
    }
  };

  if (!user || user.role !== "admin") return null;

  return (
    <div className="bg-muted min-h-screen" data-testid="admin-page">
      <div className="container-x py-12 lg:py-16">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
          <div>
            <div className="overline mb-3">Admin Console</div>
            <h1 className="font-display text-4xl lg:text-6xl font-light tracking-tighter">
              Studio <span className="italic">control room.</span>
            </h1>
          </div>
          <div className="flex gap-3">
          <div className="flex gap-3">
            <button onClick={() => navigate("/dashboard")} className="btn-outline" data-testid="back-dashboard">
              <ArrowLeft size={14} /> Dashboard
            </button>
            <button
              onClick={() => { if (showForm) { resetForm(); } else { setShowForm(true); } }}
              className="btn-primary"
              data-testid="new-project-btn"
            >
              <Plus size={14} /> {showForm ? "Cancel" : "New Project"}
            </button>
          </div>
          </div>
        </div>

        {/* New project form */}
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="bg-card border border-border mb-12"
            data-testid="new-project-form"
          >
            <div className="p-8 border-b border-border">
              <div className="overline mb-2">01 / {editingId ? "Edit Project" : "Create Portfolio Project"}</div>
              <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">
                {editingId ? form.title || "Untitled" : "Project details"}
              </h2>
            </div>
            <form onSubmit={createProject} className="p-8 space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div>
                  <label className="overline mb-3 block">Title</label>
                  <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="input-line" data-testid="form-title" />
                </div>
                <div>
                  <label className="overline mb-3 block">Category</label>
                  <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="input-line" data-testid="form-category">
                    {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="overline mb-3 block">Location</label>
                  <input required value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="input-line" data-testid="form-location" />
                </div>
                <div>
                  <label className="overline mb-3 block">Year</label>
                  <input required type="number" min="1990" max="2100" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} className="input-line" data-testid="form-year" />
                </div>
                <div className="md:col-span-2">
                  <label className="overline mb-3 block">Description</label>
                  <textarea required rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="input-line resize-none" data-testid="form-description" />
                </div>
                <div className="md:col-span-2 flex items-center gap-3">
                  <input id="featured" type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} className="w-4 h-4 accent-primary" data-testid="form-featured" />
                  <label htmlFor="featured" className="text-sm font-medium">Feature on Home page</label>
                </div>
              </div>

              {/* Cover image */}
              <div>
                <label className="overline mb-4 block">Cover image *</label>
                {form.cover_image ? (
                  <div className="relative inline-block">
                    <img src={form.cover_image} alt="Cover" className="w-64 h-40 object-cover border border-border" />
                    <button type="button" onClick={() => setForm({ ...form, cover_image: "" })} className="absolute -top-2 -right-2 w-7 h-7 bg-foreground text-background flex items-center justify-center" data-testid="remove-cover">
                      <X size={14} />
                    </button>
                  </div>
                ) : (
                  <button type="button" onClick={() => fileRef.current?.click()} className="w-64 h-40 border-2 border-dashed border-border flex flex-col items-center justify-center gap-2 hover:border-primary hover:bg-muted/40 transition-colors" data-testid="upload-cover-btn">
                    <Upload size={20} />
                    <span className="overline">Upload cover</span>
                  </button>
                )}
                <input ref={fileRef} type="file" accept="image/*" onChange={onCoverPick} className="hidden" data-testid="cover-input" />
              </div>

              {/* Gallery */}
              <div>
                <label className="overline mb-4 block">Gallery images (optional)</label>
                <div className="flex flex-wrap gap-3">
                  {form.images.map((img, i) => (
                    <div key={img} className="relative">
                      <img src={img} alt="" className="w-24 h-24 object-cover border border-border" />
                      <button type="button" onClick={() => removeGalleryImg(i)} className="absolute -top-2 -right-2 w-6 h-6 bg-foreground text-background flex items-center justify-center">
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                  <button type="button" onClick={() => galleryRef.current?.click()} className="w-24 h-24 border-2 border-dashed border-border flex flex-col items-center justify-center gap-1 hover:border-primary transition-colors" data-testid="upload-gallery-btn">
                    <Plus size={20} />
                    <span className="text-[10px] uppercase tracking-widest">Add</span>
                  </button>
                </div>
                <input ref={galleryRef} type="file" accept="image/*" multiple onChange={onGalleryPick} className="hidden" />
              </div>

              <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50" data-testid="form-submit">
                {loading ? "Saving…" : (editingId ? "Save Changes" : "Create Project")}
              </button>
            </form>
          </motion.div>
        )}

        {/* Projects table */}
        <div className="bg-card border border-border mb-12" data-testid="projects-table">
          <div className="p-8 border-b border-border flex items-center justify-between">
            <div>
              <div className="overline mb-2">02 / Portfolio Projects</div>
              <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">{projects.length} live</h2>
            </div>
          </div>
          <div className="divide-y divide-border">
            {projects.map((p) => (
              <div key={p.project_id} className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-center" data-testid={`row-${p.project_id}`}>
                <div className="lg:col-span-2">
                  <img src={p.cover_image} alt={p.title} className="w-full h-20 object-cover" />
                </div>
                <div className="lg:col-span-4">
                  <div className="font-display text-lg font-medium">{p.title}</div>
                  <div className="text-xs text-muted-foreground mt-1">{p.location}</div>
                </div>
                <div className="lg:col-span-2 text-sm uppercase tracking-widest text-muted-foreground">{p.category}</div>
                <div className="lg:col-span-1 text-sm">{p.year}</div>
                <div className="lg:col-span-1">
                  {p.featured ? (
                    <span className="inline-block px-2 py-1 bg-primary text-primary-foreground text-[10px] uppercase tracking-widest">Featured</span>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </div>
                <div className="lg:col-span-2 text-right flex justify-end gap-2">
                  <button
                    onClick={() => startEdit(p)}
                    className="w-10 h-10 border border-border hover:bg-foreground hover:text-background hover:border-foreground transition-colors inline-flex items-center justify-center"
                    data-testid={`edit-${p.project_id}`}
                    title="Edit project"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => deleteProject(p.project_id, p.title)}
                    className="w-10 h-10 border border-border hover:bg-destructive hover:text-destructive-foreground hover:border-destructive transition-colors inline-flex items-center justify-center"
                    data-testid={`delete-${p.project_id}`}
                    title="Delete project"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Inquiries */}
        <div className="bg-card border border-border" data-testid="inquiries-table">
          <div className="p-8 border-b border-border">
            <div className="overline mb-2">03 / Recent Inquiries</div>
            <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">{inquiries.length} total</h2>
          </div>
          {inquiries.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">No inquiries yet.</div>
          ) : (
            <div className="divide-y divide-border">
              {inquiries.map((iq) => (
                <div key={iq.inquiry_id} className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-4">
                  <div className="lg:col-span-3">
                    <div className="font-medium">{iq.name}</div>
                    <a href={`mailto:${iq.email}`} className="text-sm text-primary hover:underline">{iq.email}</a>
                    {iq.phone && <div className="text-xs text-muted-foreground mt-1">{iq.phone}</div>}
                  </div>
                  <div className="lg:col-span-2 text-sm">
                    <div className="overline mb-1 text-muted-foreground">Type</div>
                    {iq.project_type}
                  </div>
                  <div className="lg:col-span-2 text-sm">
                    <div className="overline mb-1 text-muted-foreground">Budget</div>
                    {iq.budget || "—"}
                  </div>
                  <div className="lg:col-span-5 text-sm">
                    <div className="overline mb-1 text-muted-foreground">Message</div>
                    <p className="line-clamp-3">{iq.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
