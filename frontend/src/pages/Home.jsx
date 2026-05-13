import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";
import api from "../lib/api";

const stats = [
  { n: "27", label: "Years Building" },
  { n: "184", label: "Completed Projects" },
  { n: "$420M", label: "Construction Value" },
  { n: "98%", label: "On-time Delivery" },
];

const services = [
  {
    n: "01",
    title: "Building Construction",
    body: "Ground-up commercial, multi-family, and mixed-use construction delivered with rigor and craft.",
  },
  {
    n: "02",
    title: "Residential Renovations",
    body: "Whole-home transformations and historic renovations led by an in-house craft team.",
  },
  {
    n: "03",
    title: "Project Management",
    body: "Owner's representative services that protect schedule, budget, and creative intent end-to-end.",
  },
];

export default function Home() {
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    api.get("/projects?featured=true").then(({ data }) => setFeatured(data)).catch(() => {});
  }, []);

  return (
    <div data-testid="home-page">
      {/* HERO */}
      <section className="relative min-h-[92vh] flex items-end overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://static.prod-images.emergentagent.com/jobs/8eec06da-b90c-4d50-ad92-3f92bed59463/images/c3a46ae542227f749e6bc57f4167f7dd3efc82844fdef44f37728f887c08021d.png"
            alt="Modern architectural residence at golden hour"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-black/10"></div>
        </div>

        <div className="relative container-x pb-20 lg:pb-32 text-white w-full">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, ease: "easeOut" }}
              className="lg:col-span-9"
            >
              <div className="overline text-white/90 mb-8">Building Co. · Denver, CO</div>
              <h1 className="font-display text-5xl sm:text-6xl lg:text-8xl xl:text-[9rem] font-light leading-[0.95] tracking-tighter">
                Structures<br />
                shaped by<br />
                <span className="italic font-light">patience.</span>
              </h1>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.3 }}
              className="lg:col-span-3 max-w-sm"
            >
              <p className="text-base text-white/80 leading-relaxed mb-6">
                A construction studio working across residential, commercial, and
                renovation—delivering 184 projects since 1998.
              </p>
              <Link to="/contact" data-testid="hero-cta" className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] border-b border-white/60 pb-1 hover:text-primary hover:border-primary transition-colors">
                Start a project <ArrowUpRight size={14} />
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* MARQUEE */}
      <section className="border-y border-border py-8 overflow-hidden bg-secondary/40">
        <div className="flex whitespace-nowrap marquee-track">
          {Array.from({ length: 2 }).map((_, gi) => (
            <div key={gi} className="flex items-center gap-12 px-6">
              {["Residential", "Commercial", "Renovation", "Historic", "Mixed-use", "Adaptive Reuse", "Hospitality"].map((w) => (
                <span key={w + gi} className="font-display italic text-3xl lg:text-5xl text-foreground/40">
                  — {w}
                </span>
              ))}
            </div>
          ))}
        </div>
      </section>

      {/* STATS */}
      <section className="container-x py-24 lg:py-32 grid grid-cols-2 lg:grid-cols-4 gap-12 border-b border-border">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: i * 0.1 }}
          >
            <div className="font-display text-5xl lg:text-7xl font-light tracking-tighter">{s.n}</div>
            <div className="overline mt-3 text-muted-foreground" style={{ color: 'hsl(var(--muted-foreground))' }}>{s.label}</div>
          </motion.div>
        ))}
      </section>

      {/* SERVICES */}
      <section className="container-x py-24 lg:py-32 grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-4">
          <div className="overline mb-6">What we build</div>
          <h2 className="font-display text-4xl lg:text-6xl font-light tracking-tighter leading-[1.02]">
            Construction with the discipline of an atelier.
          </h2>
          <Link to="/services" className="btn-outline mt-10" data-testid="home-services-link">
            All Services <ArrowRight size={14} />
          </Link>
        </div>
        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-3 gap-0 border-t border-border">
          {services.map((s) => (
            <div key={s.n} className="border-b md:border-b-0 md:border-r border-border p-8 last:border-r-0 hover:bg-muted transition-colors">
              <div className="overline mb-10">{s.n}</div>
              <h3 className="font-display text-2xl font-medium mb-4 leading-tight">{s.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURED PROJECTS */}
      <section className="bg-muted py-24 lg:py-32">
        <div className="container-x">
          <div className="flex items-end justify-between mb-16">
            <div>
              <div className="overline mb-4">Selected Work · 2023—2024</div>
              <h2 className="font-display text-4xl lg:text-6xl font-light tracking-tighter">Recent commissions</h2>
            </div>
            <Link to="/portfolio" className="hidden md:inline-flex btn-outline" data-testid="home-portfolio-link">
              Full Portfolio <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 lg:gap-8">
            {featured.slice(0, 3).map((p, i) => (
              <motion.div
                key={p.project_id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.7, delay: i * 0.15 }}
                className={
                  i === 0
                    ? "md:col-span-7 md:row-span-2"
                    : "md:col-span-5"
                }
                data-testid={`home-project-${i}`}
              >
                <Link to="/portfolio" className="group block">
                  <div className="overflow-hidden mb-5">
                    <img
                      src={p.cover_image}
                      alt={p.title}
                      className={`w-full object-cover transition-transform duration-700 group-hover:scale-105 ${
                        i === 0 ? "h-[400px] lg:h-[640px]" : "h-[300px] lg:h-[310px]"
                      }`}
                    />
                  </div>
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="overline mb-1">{p.category} · {p.year}</div>
                      <h3 className="font-display text-xl lg:text-2xl font-medium">{p.title}</h3>
                      <div className="text-sm text-muted-foreground mt-1">{p.location}</div>
                    </div>
                    <ArrowUpRight className="opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="container-x py-24 lg:py-40 border-t border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <div className="overline mb-6">Begin</div>
            <h2 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              Have a site,<br />a brief, or<br />a building?
            </h2>
          </div>
          <div className="lg:col-span-4 lg:pl-12">
            <p className="text-base text-muted-foreground mb-8">
              We typically respond within two business days. Tell us about your project, timeline, and budget — we'll do the rest.
            </p>
            <Link to="/contact" className="btn-primary" data-testid="home-cta-button">
              Start a Project <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
