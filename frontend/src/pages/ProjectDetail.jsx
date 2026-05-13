import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import api from "../lib/api";

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setNotFound(false);
    api
      .get(`/projects/${id}`)
      .then(({ data }) => {
        if (!active) return;
        setProject(data);
        return api.get(`/projects?category=${data.category}`);
      })
      .then((res) => {
        if (!active || !res) return;
        setRelated(res.data.filter((p) => p.project_id !== id).slice(0, 3));
      })
      .catch((err) => {
        if (!active) return;
        if (err.response?.status === 404) setNotFound(true);
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [id]);

  if (loading) {
    return <div className="min-h-[60vh] flex items-center justify-center overline text-muted-foreground" data-testid="project-loading">Loading…</div>;
  }
  if (notFound || !project) {
    return (
      <div className="container-x py-32 text-center" data-testid="project-notfound">
        <div className="overline mb-4">404</div>
        <h1 className="font-display text-4xl mb-6">Project not found</h1>
        <Link to="/portfolio" className="btn-outline">Back to Portfolio</Link>
      </div>
    );
  }

  return (
    <div data-testid="project-detail">
      {/* Hero */}
      <section className="relative h-[60vh] lg:h-[85vh] overflow-hidden">
        <img src={project.cover_image} alt={project.title} className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
        <div className="relative container-x h-full flex items-end pb-12 lg:pb-20 text-white">
          <div>
            <button onClick={() => navigate(-1)} className="text-xs font-bold uppercase tracking-[0.2em] inline-flex items-center gap-2 mb-6 hover:text-primary transition-colors" data-testid="back-button">
              <ArrowLeft size={14} /> Back
            </button>
            <div className="overline text-white/80 mb-4">{project.category} · {project.year}</div>
            <h1 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              {project.title}
            </h1>
          </div>
        </div>
      </section>

      {/* Meta */}
      <section className="container-x py-20 lg:py-28 border-b border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-4 lg:col-start-1 space-y-10">
            <div>
              <div className="overline mb-3 text-muted-foreground">Location</div>
              <div className="font-display text-2xl">{project.location}</div>
            </div>
            <div>
              <div className="overline mb-3 text-muted-foreground">Typology</div>
              <div className="font-display text-2xl capitalize">{project.category}</div>
            </div>
            <div>
              <div className="overline mb-3 text-muted-foreground">Year completed</div>
              <div className="font-display text-2xl">{project.year}</div>
            </div>
            {project.featured && (
              <div className="overline text-primary">Featured Work</div>
            )}
          </div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-7 lg:col-start-6"
          >
            <div className="overline mb-6">The brief</div>
            <p className="font-display text-2xl lg:text-4xl font-light tracking-tight leading-[1.2]">
              {project.description}
            </p>
          </motion.div>
        </div>
      </section>

      {/* Gallery */}
      {project.images && project.images.length > 0 && (
        <section className="bg-muted py-20 lg:py-28">
          <div className="container-x">
            <div className="overline mb-12">Gallery</div>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 lg:gap-8">
              {project.images.map((img, i) => (
                <motion.div
                  key={img}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: (i % 6) * 0.08 }}
                  className={i % 3 === 0 ? "md:col-span-7" : "md:col-span-5"}
                  data-testid={`gallery-${i}`}
                >
                  <img src={img} alt={`${project.title} ${i + 1}`} className="w-full h-[400px] lg:h-[520px] object-cover" />
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="container-x py-20 lg:py-32 border-b border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <div className="overline mb-6">Begin yours</div>
            <h2 className="font-display text-4xl lg:text-7xl font-light tracking-tighter leading-[0.95]">
              Like this project?<br/>
              <span className="italic">Let's talk.</span>
            </h2>
          </div>
          <div className="lg:col-span-4">
            <p className="text-base text-muted-foreground mb-8">
              Most of our work begins with a single conversation. Share your site,
              brief, or budget — we'll respond within two business days.
            </p>
            <Link to="/contact" className="btn-primary" data-testid="cta-contact">
              Start a Project <ArrowUpRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* Related */}
      {related.length > 0 && (
        <section className="container-x py-20 lg:py-28">
          <div className="overline mb-12">More {project.category} work</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {related.map((p, i) => (
              <motion.div
                key={p.project_id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.08 }}
              >
                <Link to={`/portfolio/${p.project_id}`} className="group block" data-testid={`related-${p.project_id}`}>
                  <div className="overflow-hidden mb-4">
                    <img src={p.cover_image} alt={p.title} className="w-full h-[280px] object-cover transition-transform duration-700 group-hover:scale-105" />
                  </div>
                  <div className="overline mb-1">{p.category} · {p.year}</div>
                  <h3 className="font-display text-xl font-medium">{p.title}</h3>
                  <div className="text-sm text-muted-foreground mt-1">{p.location}</div>
                </Link>
              </motion.div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
