import { motion } from "framer-motion";
import { Check } from "lucide-react";
import SEO from "../components/SEO";

const services = [
  {
    n: "01",
    title: "Building Construction",
    summary:
      "Ground-up commercial, multi-family, and mixed-use construction at scale.",
    description:
      "From foundation excavation through final commissioning, we deliver ground-up projects with an in-house superintendence team and an exacting set of trade partners. We specialize in mass timber, hybrid steel, and reinforced concrete.",
    deliverables: [
      "Site logistics & preconstruction",
      "Self-performed concrete & framing",
      "MEP coordination via BIM 360",
      "Commissioning & punch-list closeout",
    ],
    image:
      "https://images.unsplash.com/photo-1710701455648-e85f21bf3a79?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
  },
  {
    n: "02",
    title: "Residential Renovations",
    summary:
      "Whole-home transformations, additions, and historic restorations.",
    description:
      "Renovations require a different discipline — surgical demolition, dust-controlled site protocols, and craft trades that respect the building you already love. Our team holds historic preservation certifications across CO, NM, and UT.",
    deliverables: [
      "Whole-home gut renovations",
      "Historic restoration & preservation",
      "ADUs, additions, & garage studios",
      "Kitchen, bath, & millwork",
    ],
    image:
      "https://images.unsplash.com/photo-1681216868987-b7268753b81c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85",
  },
  {
    n: "03",
    title: "Project Management",
    summary:
      "Owner's representative services for institutional and private clients.",
    description:
      "Sometimes a project doesn't need a builder — it needs an advocate. We act as your owner's representative, managing architects, consultants, and contractors so your project arrives on schedule, on budget, and on design.",
    deliverables: [
      "Owner's representative & PM",
      "Schedule & cost control",
      "Contractor & consultant procurement",
      "Risk & change-order management",
    ],
    image:
      "https://images.pexels.com/photos/946310/pexels-photo-946310.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
  },
];

export default function Services() {
  return (
    <div data-testid="services-page">
      <SEO
        title="Services · Construction, Renovation, Project Management"
        description="Three disciplines, one studio. Stonebridge delivers ground-up construction, residential renovations, and owner's-representative project management."
        path="/services"
      />
      <section className="container-x pt-20 pb-24 lg:pt-32 lg:pb-32 border-b border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <div className="overline mb-6">Capabilities</div>
            <h1 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              Three disciplines.<br />
              <span className="italic">One studio.</span>
            </h1>
          </div>
          <div className="lg:col-span-4">
            <p className="text-base text-muted-foreground leading-relaxed">
              We organize our practice around three tightly-scoped services so every
              project gets the team and tooling it actually needs — not what's
              convenient for us.
            </p>
          </div>
        </div>
      </section>

      {services.map((svc, i) => (
        <section key={svc.n} className={`${i % 2 === 0 ? "" : "bg-muted"} py-24 lg:py-32`}>
          <div className="container-x grid grid-cols-1 lg:grid-cols-12 gap-12">
            <motion.div
              initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7 }}
              className={`lg:col-span-7 ${i % 2 === 0 ? "lg:order-1" : "lg:order-2"}`}
            >
              <img src={svc.image} alt={svc.title} className="w-full h-[400px] lg:h-[600px] object-cover" />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.7, delay: 0.15 }}
              className={`lg:col-span-5 flex flex-col justify-center ${i % 2 === 0 ? "lg:order-2" : "lg:order-1"}`}
              data-testid={`service-${svc.n}`}
            >
              <div className="overline mb-6">{svc.n} / Service</div>
              <h2 className="font-display text-3xl lg:text-5xl font-light tracking-tighter leading-tight mb-6">
                {svc.title}
              </h2>
              <p className="text-base text-muted-foreground leading-relaxed mb-8">
                {svc.description}
              </p>
              <ul className="space-y-3 border-t border-border pt-6">
                {svc.deliverables.map((d) => (
                  <li key={d} className="flex items-start gap-3 text-sm">
                    <Check size={16} className="mt-1 text-primary shrink-0" />
                    <span>{d}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </section>
      ))}
    </div>
  );
}
