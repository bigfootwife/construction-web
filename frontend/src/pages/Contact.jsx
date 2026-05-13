import { useState } from "react";
import { toast } from "sonner";
import { ArrowRight, Check } from "lucide-react";
import { motion } from "framer-motion";
import api from "../lib/api";
import SEO from "../components/SEO";

const PROJECT_TYPES = ["New Construction", "Residential Renovation", "Commercial Build-out", "Project Management", "Other"];
const BUDGETS = ["< $250K", "$250K — $1M", "$1M — $5M", "$5M+", "Not sure yet"];

export default function Contact() {
  const [form, setForm] = useState({
    name: "", email: "", phone: "", project_type: PROJECT_TYPES[0], budget: BUDGETS[0], message: "",
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const onChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post("/inquiries", form);
      setSubmitted(true);
      toast.success("Inquiry received. We'll be in touch within 2 business days.");
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : "Could not send inquiry. Try again.";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="contact-page">
      <SEO
        title="Contact · Start a project"
        description="Tell us about your project — site, brief, timeline, and budget. Most inquiries get a partner response within two business days."
        path="/contact"
      />
      <section className="container-x pt-20 pb-16 lg:pt-32 lg:pb-20 border-b border-border">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          <div className="lg:col-span-8">
            <div className="overline mb-6">Inquire</div>
            <h1 className="font-display text-5xl lg:text-8xl font-light tracking-tighter leading-[0.95]">
              Tell us about<br />
              your <span className="italic">project.</span>
            </h1>
          </div>
          <div className="lg:col-span-4">
            <p className="text-base text-muted-foreground leading-relaxed">
              Replies within two business days. For urgent matters, call our studio
              directly at <span className="text-foreground font-medium">(303) 555-0182</span>.
            </p>
          </div>
        </div>
      </section>

      <section className="container-x py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-20">
          {/* Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-8"
          >
            {submitted ? (
              <div className="border border-border p-12 lg:p-16 bg-card" data-testid="contact-success">
                <Check size={32} className="text-primary mb-6" />
                <h2 className="font-display text-3xl lg:text-4xl font-light tracking-tighter mb-4">Inquiry received.</h2>
                <p className="text-muted-foreground max-w-md">
                  Thank you for reaching out. A partner will review your project and respond
                  within two business days.
                </p>
                <button onClick={() => { setSubmitted(false); setForm({ name: "", email: "", phone: "", project_type: PROJECT_TYPES[0], budget: BUDGETS[0], message: "" }); }} className="btn-outline mt-10">
                  Send Another
                </button>
              </div>
            ) : (
              <form onSubmit={submit} className="space-y-10" data-testid="contact-form">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                  <div>
                    <label className="overline mb-3 block">01 / Full Name</label>
                    <input
                      type="text" required value={form.name} onChange={onChange("name")}
                      className="input-line" placeholder="Your name" data-testid="contact-name"
                    />
                  </div>
                  <div>
                    <label className="overline mb-3 block">02 / Email</label>
                    <input
                      type="email" required value={form.email} onChange={onChange("email")}
                      className="input-line" placeholder="you@example.com" data-testid="contact-email"
                    />
                  </div>
                  <div>
                    <label className="overline mb-3 block">03 / Phone</label>
                    <input
                      type="tel" value={form.phone} onChange={onChange("phone")}
                      className="input-line" placeholder="(optional)" data-testid="contact-phone"
                    />
                  </div>
                  <div>
                    <label className="overline mb-3 block">04 / Project Type</label>
                    <select
                      value={form.project_type} onChange={onChange("project_type")}
                      className="input-line" data-testid="contact-project-type"
                    >
                      {PROJECT_TYPES.map((p) => <option key={p}>{p}</option>)}
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="overline mb-3 block">05 / Estimated Budget</label>
                    <div className="flex flex-wrap gap-3">
                      {BUDGETS.map((b) => (
                        <button
                          key={b} type="button" onClick={() => setForm({ ...form, budget: b })}
                          data-testid={`budget-${b}`}
                          className={`px-5 py-2.5 border text-xs font-bold uppercase tracking-[0.15em] transition-all ${
                            form.budget === b ? "bg-foreground text-background border-foreground" : "border-border hover:border-foreground"
                          }`}
                        >
                          {b}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="overline mb-3 block">06 / Tell us about your project</label>
                  <textarea
                    required value={form.message} onChange={onChange("message")}
                    rows={6} className="input-line resize-none"
                    placeholder="Site, scope, timeline, anything we should know…"
                    data-testid="contact-message"
                  />
                </div>

                <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50" data-testid="contact-submit">
                  {loading ? "Sending…" : "Send Inquiry"} <ArrowRight size={14} />
                </button>
              </form>
            )}
          </motion.div>

          {/* Side info */}
          <aside className="lg:col-span-4 lg:border-l lg:border-border lg:pl-12 space-y-12">
            <div>
              <div className="overline mb-4">Studio</div>
              <p className="text-base">1842 Larimer St, Floor 4<br/>Denver, CO 80202</p>
            </div>
            <div>
              <div className="overline mb-4">Direct</div>
              <p className="text-base"><a href="mailto:hello@stonebridge.com" className="hover:text-primary">hello@stonebridge.com</a></p>
              <p className="text-base mt-1">(303) 555-0182</p>
            </div>
            <div>
              <div className="overline mb-4">Hours</div>
              <p className="text-base text-muted-foreground">Mon — Fri · 8a — 6p MT</p>
            </div>
            <div>
              <div className="overline mb-4">Service Region</div>
              <p className="text-base text-muted-foreground">Colorado · New Mexico · Utah · Wyoming</p>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
