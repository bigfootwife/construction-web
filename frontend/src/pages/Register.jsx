import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/dashboard");
    } catch (err) {
      const d = err.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "Could not register.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-x py-20 lg:py-32 grid grid-cols-1 lg:grid-cols-12 gap-12" data-testid="register-page">
      <div className="lg:col-span-5 flex flex-col justify-center">
        <div className="overline mb-6">Open a Client Account</div>
        <h1 className="font-display text-4xl lg:text-6xl font-light tracking-tighter leading-[1] mb-10">
          Track your<br />project.
        </h1>

        <form onSubmit={submit} className="space-y-8" data-testid="register-form">
          <div>
            <label className="overline mb-3 block">Full Name</label>
            <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-line" data-testid="register-name" />
          </div>
          <div>
            <label className="overline mb-3 block">Email</label>
            <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-line" data-testid="register-email" />
          </div>
          <div>
            <label className="overline mb-3 block">Password</label>
            <input type="password" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input-line" data-testid="register-password" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50" data-testid="register-submit">
            {loading ? "Creating…" : "Create Account"} <ArrowRight size={14} />
          </button>
        </form>

        <p className="mt-10 text-sm text-muted-foreground">
          Already a client?{" "}
          <Link to="/login" className="text-foreground border-b border-foreground/40 hover:border-foreground" data-testid="login-link-from-register">Sign in</Link>
        </p>
      </div>
      <div className="lg:col-span-7 hidden lg:block">
        <img
          src="https://images.unsplash.com/photo-1710701455648-e85f21bf3a79?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MDV8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhcmNoaXRlY3R1cmUlMjBidWlsZGluZyUyMGV4dGVyaW9yfGVufDB8fHx8MTc3ODY1OTE2Nnww&ixlib=rb-4.1.0&q=85"
          alt="Architectural building"
          className="w-full h-full object-cover max-h-[700px]"
        />
      </div>
    </div>
  );
}
