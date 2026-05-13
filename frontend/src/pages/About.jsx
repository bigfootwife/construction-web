import { motion } from "framer-motion";
import SEO from "../components/SEO";

const values = [
  { n: "01", title: "Build slowly, well.", body: "We turn down 7 in 10 projects to keep our portfolio small and our team focused." },
  { n: "02", title: "Craft over scale.", body: "An in-house team of carpenters, masons, and finish specialists who care about the joinery." },
  { n: "03", title: "Documentation as art.", body: "Every project ships with a printed monograph: drawings, materials, photography." },
  { n: "04", title: "Owner's first.", body: "Transparent budgets, fixed margins, and a single point of contact from concept through warranty." },
];

const timeline = [
  { year: "1998", text: "Founded in a converted warehouse on Larimer Street as a residential renovation outfit." },
  { year: "2006", text: "Expanded into commercial construction with the Northgate I commercial tower." },
  { year: "2014", text: "Launched the owner's representation practice for institutional clients." },
  { year: "2020", text: "Opened the Boulder timber yard and millwork facility." },
  { year: "2024", text: "Completed 184th project — recipient of the AIA Mountain Region Honor Award." },
];

const team = [
  { name: "Margaret Holloway", role: "Founding Partner", img: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&q=80" },
  { name: "Daniel Park", role: "Partner, Construction", img: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80" },
  { name: "Aisha Bennett", role: "Director, Renovations", img: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=600&q=80" },
  { name: "Carlos Reyes", role: "Director, Project Management", img: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=600&q=80" },
];

export default function About() {
  return (
    <div data-testid="about-page">
      <SEO
        title="About · 48 builders, 27 years"
        description="Founded in 1998, Stonebridge is a 48-person construction practice based in Denver. Meet our four founding partners and read our brief history."
        path="/about"
      />
      {/* Intro */}
      <section className="container-x pt-20 pb-24 lg:pt-32 lg:pb-32">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-7">
            <div className="overline mb-6">Studio · Est. 1998</div>
            <h1 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              A practice<br />
              of <span className="italic">forty-eight</span><br />
              builders.
            </h1>
          </div>
          <div className="lg:col-span-5 lg:pt-32">
            <p className="text-lg text-muted-foreground leading-relaxed">
              Stonebridge is a Denver-based construction studio operating across
              residential, commercial, and renovation work — held together by a
              shared belief that building well is, above all, a slow act of
              attention.
            </p>
          </div>
        </div>
      </section>

      {/* Image */}
      <section className="container-x">
        <img
          src="https://images.unsplash.com/photo-1756227584303-f1400daaa69d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85"
          alt="Stonebridge project"
          className="w-full h-[500px] lg:h-[700px] object-cover"
        />
      </section>

      {/* Values */}
      <section className="container-x py-24 lg:py-32">
        <div className="overline mb-6">How we work</div>
        <h2 className="font-display text-4xl lg:text-6xl font-light tracking-tighter mb-16 max-w-3xl">
          Four operating principles.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-0 border-t border-border">
          {values.map((v, i) => (
            <motion.div
              key={v.n}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              className={`p-10 lg:p-12 border-b border-border ${i % 2 === 0 ? "md:border-r" : ""}`}
            >
              <div className="overline mb-8">{v.n}</div>
              <h3 className="font-display text-2xl lg:text-3xl font-medium mb-4 tracking-tight">{v.title}</h3>
              <p className="text-base text-muted-foreground leading-relaxed">{v.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Timeline */}
      <section className="bg-muted py-24 lg:py-32">
        <div className="container-x">
          <div className="overline mb-6">A short history</div>
          <h2 className="font-display text-4xl lg:text-6xl font-light tracking-tighter mb-16 max-w-3xl">
            Twenty-seven years, mostly on site.
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {timeline.map((t, i) => (
              <motion.div
                key={t.year}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="lg:col-span-3 border-t border-foreground pt-6"
              >
                <div className="font-display text-3xl font-light tracking-tight mb-4">{t.year}</div>
                <p className="text-sm text-muted-foreground leading-relaxed">{t.text}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="container-x py-24 lg:py-32">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end mb-16">
          <div className="lg:col-span-8">
            <div className="overline mb-6">The Partners</div>
            <h2 className="font-display text-4xl lg:text-6xl font-light tracking-tighter">
              Forty-eight people. Four leads.
            </h2>
          </div>
          <div className="lg:col-span-4">
            <p className="text-base text-muted-foreground">
              Every project is led personally by a partner. You'll know exactly who
              to call.
            </p>
          </div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {team.map((m, i) => (
            <motion.div
              key={m.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: i * 0.08 }}
            >
              <div className="overflow-hidden mb-4">
                <img src={m.img} alt={m.name} className="w-full h-[280px] lg:h-[380px] object-cover grayscale hover:grayscale-0 transition-all duration-700" />
              </div>
              <h3 className="font-display text-lg font-medium">{m.name}</h3>
              <div className="text-sm text-muted-foreground">{m.role}</div>
            </motion.div>
          ))}
        </div>
      </section>
    </div>
  );
}
