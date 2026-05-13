import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { motion } from "framer-motion";
import { LogOut, Calendar, FileText, MessageSquare, Hammer } from "lucide-react";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState([]);
  const [inquiries, setInquiries] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/client/projects").then(({ data }) => setProjects(data)).catch(() => {});
    if (user?.role === "admin") {
      api.get("/inquiries").then(({ data }) => setInquiries(data)).catch(() => {});
    }
  }, [user]);

  const onLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="bg-muted min-h-screen" data-testid="dashboard-page">
      <div className="container-x py-12 lg:py-16">
        {/* Header */}
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
            { icon: <FileText size={18} />, label: "Documents", value: "12" },
            { icon: <MessageSquare size={18} />, label: "Unread Messages", value: user?.role === "admin" ? inquiries.filter(i => i.status === "new").length : 0 },
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
                <div className="overline">{i < 9 ? `0${i + 1}` : i + 1}</div>
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
                <div key={p.cp_id} className="p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center" data-testid={`project-${p.cp_id}`}>
                  <div className="lg:col-span-5">
                    <div className="overline mb-2">{p.project_type}</div>
                    <h3 className="font-display text-xl lg:text-2xl font-medium tracking-tight">{p.title}</h3>
                    <p className="text-sm text-muted-foreground mt-2 max-w-md">{p.notes}</p>
                  </div>
                  <div className="lg:col-span-4">
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
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Admin Inquiries */}
        {user?.role === "admin" && (
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
