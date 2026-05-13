import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { X, ArrowUpRight } from "lucide-react";
import api from "../lib/api";

const filters = [
  { id: "all", label: "All Work" },
  { id: "residential", label: "Residential" },
  { id: "commercial", label: "Commercial" },
  { id: "renovation", label: "Renovation" },
];

export default function Portfolio() {
  const [projects, setProjects] = useState([]);
  const [filter, setFilter] = useState("all");
  const [active, setActive] = useState(null);

  useEffect(() => {
    api
      .get(`/projects${filter !== "all" ? `?category=${filter}` : ""}`)
      .then(({ data }) => setProjects(data))
      .catch(() => setProjects([]));
  }, [filter]);

  return (
    <div data-testid="portfolio-page">
      <section className="container-x pt-20 pb-16 lg:pt-32 lg:pb-20 border-b border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <div className="overline mb-6">Selected Works · 1998—2025</div>
            <h1 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              Built portfolio.
            </h1>
          </div>
          <div className="lg:col-span-4">
            <p className="text-base text-muted-foreground leading-relaxed">
              A curated selection from 184 completed projects. Filter by typology or
              click any project to view the brief.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 mt-16">
          {filters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              data-testid={`filter-${f.id}`}
              className={`px-5 py-3 border text-xs font-bold uppercase tracking-[0.18em] transition-all ${
                filter === f.id
                  ? "bg-foreground text-background border-foreground"
                  : "border-border hover:border-foreground"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </section>

      <section className="container-x py-16 lg:py-24">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-12">
          <AnimatePresence mode="popLayout">
            {projects.map((p, i) => (
              <motion.button
                key={p.project_id}
                layout
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5, delay: (i % 9) * 0.06 }}
                onClick={() => setActive(p)}
                data-testid={`portfolio-card-${p.project_id}`}
                className="group text-left"
              >
                <div className="overflow-hidden mb-4">
                  <img
                    src={p.cover_image}
                    alt={p.title}
                    className="w-full h-[340px] object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                </div>
                <div className="flex justify-between items-start">
                  <div>
                    <div className="overline mb-1">{p.category} · {p.year}</div>
                    <h3 className="font-display text-xl font-medium">{p.title}</h3>
                    <div className="text-sm text-muted-foreground mt-1">{p.location}</div>
                  </div>
                </div>
              </motion.button>
            ))}
          </AnimatePresence>
        </div>
        {projects.length === 0 && (
          <div className="text-center py-32 overline text-muted-foreground">No projects in this category yet.</div>
        )}
      </section>

      {/* Lightbox */}
      <AnimatePresence>
        {active && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-md overflow-y-auto"
            onClick={() => setActive(null)}
            data-testid="portfolio-lightbox"
          >
            <div className="container-x py-16 lg:py-24" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setActive(null)}
                className="fixed top-8 right-8 z-10 w-12 h-12 border border-foreground flex items-center justify-center hover:bg-foreground hover:text-background transition-colors"
                data-testid="lightbox-close"
              >
                <X size={18} />
              </button>
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                <div className="lg:col-span-8">
                  <img src={active.cover_image} alt={active.title} className="w-full h-auto" />
                </div>
                <div className="lg:col-span-4">
                  <div className="overline mb-4">{active.category} · {active.year}</div>
                  <h2 className="font-display text-4xl lg:text-5xl font-light tracking-tighter mb-6">{active.title}</h2>
                  <p className="overline mb-2 text-muted-foreground">Location</p>
                  <p className="mb-8">{active.location}</p>
                  <p className="overline mb-2 text-muted-foreground">Brief</p>
                  <p className="text-base text-muted-foreground leading-relaxed">{active.description}</p>
                  <Link
                    to={`/portfolio/${active.project_id}`}
                    className="btn-primary mt-10"
                    data-testid="lightbox-view-detail"
                  >
                    View Project <ArrowUpRight size={14} />
                  </Link>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
