import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useConfirm } from "../hooks/useConfirm";
import api from "../lib/api";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  LogOut, Calendar, FileText, MessageSquare, Hammer,
  Download, Trash2, Plus, Upload, File as FileIcon, ChevronDown, ChevronRight,
} from "lucide-react";
import CommentsThread from "../components/CommentsThread";
import SEO from "../components/SEO";

function formatBytes(b) {
  if (!b) return "—";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

function DocumentRow({ doc, isAdmin, onDelete }) {
  return (
    <div className="p-5 grid grid-cols-1 md:grid-cols-12 gap-3 items-center" data-testid={`doc-${doc.doc_id}`}>
      <div className="md:col-span-1 flex justify-center md:justify-start">
        <div className="w-10 h-10 border border-border flex items-center justify-center text-primary">
          <FileIcon size={16} />
        </div>
      </div>
      <div className="md:col-span-6">
        <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="font-medium hover:text-primary transition-colors" data-testid={`doc-link-${doc.doc_id}`}>
          {doc.title}
        </a>
        <div className="text-xs text-muted-foreground mt-1">
          {doc.file_type?.split("/")[1]?.toUpperCase() || "FILE"} · {formatBytes(doc.size)}
        </div>
      </div>
      <div className="md:col-span-3 text-xs text-muted-foreground">
        {new Date(doc.uploaded_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })}
      </div>
      <div className="md:col-span-2 flex justify-end gap-2">
        <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="w-9 h-9 border border-border hover:bg-foreground hover:text-background transition-colors inline-flex items-center justify-center" title="Open">
          <Download size={14} />
        </a>
        {isAdmin && (
          <button onClick={() => onDelete(doc)} className="w-9 h-9 border border-border hover:bg-destructive hover:text-destructive-foreground hover:border-destructive transition-colors inline-flex items-center justify-center" data-testid={`doc-delete-${doc.doc_id}`} title="Delete">
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

function UploadDocumentForm({ projects, onUploaded }) {
  const [open, setOpen] = useState(false);
  const [cpId, setCpId] = useState(projects[0]?.cp_id || "");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);

  const submit = async (e) => {
    e.preventDefault();
    if (!file || !cpId || !title.trim()) {
      toast.error("Title, file and project are required.");
      return;
    }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const up = await api.post("/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await api.post("/client/documents", {
        cp_id: cpId,
        title: title.trim(),
        file_url: up.data.url,
        file_type: file.type,
        size: file.size,
      });
      toast.success("Document attached.");
      setTitle(""); setFile(null); setOpen(false);
      onUploaded?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed.");
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="btn-outline" data-testid="open-doc-upload">
        <Plus size={14} /> Attach Document
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="bg-muted p-6 border border-border space-y-5" data-testid="doc-upload-form">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="overline mb-2 block">Project</label>
          <select value={cpId} onChange={(e) => setCpId(e.target.value)} className="input-line" data-testid="doc-cp">
            {projects.map((p) => <option key={p.cp_id} value={p.cp_id}>{p.title} — {p.client_email}</option>)}
          </select>
        </div>
        <div>
          <label className="overline mb-2 block">Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} className="input-line" placeholder="e.g. Construction Agreement" data-testid="doc-title" />
        </div>
      </div>
      <div>
        <label className="overline mb-2 block">File</label>
        <input ref={inputRef} type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="hidden" data-testid="doc-file" />
        <button type="button" onClick={() => inputRef.current?.click()} className="btn-outline">
          <Upload size={14} /> {file ? file.name : "Choose file"}
        </button>
      </div>
      <div className="flex gap-3">
        <button type="submit" disabled={busy} className="btn-primary disabled:opacity-50" data-testid="doc-submit">
          {busy ? "Uploading…" : "Attach"}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="btn-outline">Cancel</button>
      </div>
    </form>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const confirm = useConfirm();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [inquiries, setInquiries] = useState([]);

  const refresh = () => {
    api.get("/client/projects").then(({ data }) => setProjects(data)).catch(() => {});
    api.get("/client/documents").then(({ data }) => setDocuments(data)).catch(() => {});
    if (user?.role === "admin") {
      api.get("/inquiries").then(({ data }) => setInquiries(data)).catch(() => {});
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const onLogout = async () => {
    await logout();
    navigate("/");
  };

  const deleteDoc = async (doc) => {
    const ok = await confirm({
      title: "Delete document?",
      description: `"${doc.title}" will be removed and its file made unavailable.`,
      confirmLabel: "Delete",
      destructive: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/client/documents/${doc.doc_id}`);
      toast.success("Document deleted.");
      refresh();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed.");
    }
  };

  const isAdmin = user?.role === "admin";
  const [openComments, setOpenComments] = useState({});
  const toggleComments = (cpId) => setOpenComments((o) => ({ ...o, [cpId]: !o[cpId] }));
  const docsByProject = projects.reduce((acc, p) => {
    acc[p.cp_id] = documents.filter((d) => d.cp_id === p.cp_id);
    return acc;
  }, {});

  return (
    <div className="bg-muted min-h-screen" data-testid="dashboard-page">
      <SEO title="Client Dashboard" path="/dashboard" />
      <div className="container-x py-12 lg:py-16">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-12">
          <div>
            <div className="overline mb-3">Client Dashboard</div>
            <h1 className="font-display text-4xl lg:text-6xl font-light tracking-tighter">
              Hello, <span className="italic">{user?.name?.split(" ")[0] || "Client"}.</span>
            </h1>
            <p className="text-muted-foreground mt-2">{user?.email} · {user?.role}</p>
          </div>
          <button onClick={onLogout} className="btn-outline" data-testid="logout-button">
            <LogOut size={14} /> Sign Out
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-12">
          {[
            { icon: <Hammer size={18} />, label: "Active Projects", value: projects.length },
            { icon: <Calendar size={18} />, label: "Next Milestone", value: projects[0]?.next_milestone_date || "—" },
            { icon: <FileText size={18} />, label: "Documents", value: documents.length },
            { icon: <MessageSquare size={18} />, label: isAdmin ? "New Inquiries" : "Updates", value: isAdmin ? inquiries.filter(i => i.status === "new").length : projects.length },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-card border border-border p-6"
              data-testid={`stat-${i}`}
            >
              <div className="flex items-center justify-between mb-6 text-primary">
                {s.icon}
                <div className="overline">0{i + 1}</div>
              </div>
              <div className="font-display text-2xl lg:text-3xl font-medium tracking-tight">{s.value}</div>
              <div className="overline mt-2 text-muted-foreground">{s.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Projects */}
        <div className="bg-card border border-border" data-testid="dashboard-projects">
          <div className="p-8 border-b border-border flex items-center justify-between">
            <div>
              <div className="overline mb-2">Your Projects</div>
              <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">Live status</h2>
            </div>
          </div>
          {projects.length === 0 ? (
            <div className="p-16 text-center">
              <p className="text-muted-foreground">No active projects assigned to your account yet.</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {projects.map((p) => (
                <div key={p.cp_id} data-testid={`project-${p.cp_id}`}>
                  <div className="p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                    <div className="lg:col-span-5">
                      <div className="overline mb-2">{p.project_type}</div>
                      <h3 className="font-display text-xl lg:text-2xl font-medium tracking-tight">{p.title}</h3>
                      <p className="text-sm text-muted-foreground mt-2 max-w-md">{p.notes}</p>
                    </div>
                    <div className="lg:col-span-3">
                      <div className="overline mb-2 text-muted-foreground">Progress · {p.status}</div>
                      <div className="h-2 bg-secondary">
                        <div className="h-full bg-primary transition-all duration-700" style={{ width: `${p.progress}%` }} />
                      </div>
                      <div className="text-xs mt-2 text-muted-foreground">{p.progress}% complete</div>
                    </div>
                    <div className="lg:col-span-3">
                      <div className="overline mb-2 text-muted-foreground">Next Milestone</div>
                      <div className="text-sm font-medium">{p.next_milestone}</div>
                      <div className="text-xs text-muted-foreground mt-1">{p.next_milestone_date}</div>
                    </div>
                    <div className="lg:col-span-1 flex justify-end">
                      <button
                        onClick={() => toggleComments(p.cp_id)}
                        className="text-xs font-bold uppercase tracking-[0.15em] inline-flex items-center gap-1 hover:text-primary transition-colors"
                        data-testid={`toggle-comments-${p.cp_id}`}
                      >
                        {openComments[p.cp_id] ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        Talk
                      </button>
                    </div>
                  </div>
                  {openComments[p.cp_id] && (
                    <CommentsThread cpId={p.cp_id} user={user} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Documents */}
        <div className="bg-card border border-border mt-12" data-testid="dashboard-documents">
          <div className="p-8 border-b border-border flex flex-col md:flex-row md:items-end md:justify-between gap-4">
            <div>
              <div className="overline mb-2">Documents</div>
              <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">
                {documents.length} on file
              </h2>
            </div>
            {isAdmin && projects.length > 0 && (
              <UploadDocumentForm projects={projects} onUploaded={refresh} />
            )}
          </div>

          {documents.length === 0 ? (
            <div className="p-16 text-center text-muted-foreground">
              {isAdmin
                ? "No documents yet. Click 'Attach Document' to upload one."
                : "Your studio will share documents here as the project progresses."}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {projects.map((p) => {
                const list = docsByProject[p.cp_id] || [];
                if (list.length === 0) return null;
                return (
                  <div key={p.cp_id} className="p-2">
                    <div className="overline px-5 pt-5 pb-3 text-muted-foreground">{p.title}</div>
                    <div className="divide-y divide-border">
                      {list.map((doc) => (
                        <DocumentRow key={doc.doc_id} doc={doc} isAdmin={isAdmin} onDelete={deleteDoc} />
                      ))}
                    </div>
                  </div>
                );
              })}
              {/* Orphan docs (no matching project in current scope) */}
              {documents.filter((d) => !projects.some((p) => p.cp_id === d.cp_id)).map((doc) => (
                <DocumentRow key={doc.doc_id} doc={doc} isAdmin={isAdmin} onDelete={deleteDoc} />
              ))}
            </div>
          )}
        </div>

        {/* Admin Inquiries */}
        {isAdmin && (
          <div className="bg-card border border-border mt-12" data-testid="admin-inquiries">
            <div className="p-8 border-b border-border">
              <div className="overline mb-2">Admin · Recent Inquiries</div>
              <h2 className="font-display text-2xl lg:text-3xl font-medium tracking-tight">Incoming leads</h2>
            </div>
            {inquiries.length === 0 ? (
              <div className="p-16 text-center text-muted-foreground">No inquiries yet.</div>
            ) : (
              <div className="divide-y divide-border">
                {inquiries.slice(0, 8).map((iq) => (
                  <div key={iq.inquiry_id} className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-4 items-start" data-testid={`inquiry-${iq.inquiry_id}`}>
                    <div className="lg:col-span-3">
                      <div className="font-medium">{iq.name}</div>
                      <div className="text-sm text-muted-foreground">{iq.email}</div>
                    </div>
                    <div className="lg:col-span-2 text-sm">{iq.project_type}</div>
                    <div className="lg:col-span-2 text-sm">{iq.budget}</div>
                    <div className="lg:col-span-4 text-sm text-muted-foreground line-clamp-2">{iq.message}</div>
                    <div className="lg:col-span-1 overline text-primary">{iq.status}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
