import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("client@stonebridge.com");
  const [password, setPassword] = useState("Client@1234");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      const dest = location.state?.from || "/dashboard";
      navigate(dest);
    } catch (err) {
      const d = err.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const googleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="container-x py-20 lg:py-32 grid grid-cols-1 lg:grid-cols-12 gap-12" data-testid="login-page">
      <div className="lg:col-span-7 hidden lg:block">
        <img
          src="https://static.prod-images.emergentagent.com/jobs/8eec06da-b90c-4d50-ad92-3f92bed59463/images/8c4cce38ea23074c4cabf13d17c54ad297eab65936b8dcc572414fc8add3732e.png"
          alt="Architectural shapes"
          className="w-full h-full object-cover max-h-[700px]"
        />
      </div>
      <div className="lg:col-span-5 flex flex-col justify-center">
        <div className="overline mb-6">Client Portal</div>
        <h1 className="font-display text-4xl lg:text-6xl font-light tracking-tighter leading-[1] mb-10">
          Welcome<br />back.
        </h1>

        <form onSubmit={submit} className="space-y-8" data-testid="login-form">
          <div>
            <label className="overline mb-3 block">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-line" data-testid="login-email" />
          </div>
          <div>
            <label className="overline mb-3 block">Password</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="input-line" data-testid="login-password" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary disabled:opacity-50" data-testid="login-submit">
            {loading ? "Signing in…" : "Sign In"} <ArrowRight size={14} />
          </button>
        </form>

        <div className="flex items-center my-10 gap-4">
          <div className="flex-1 h-px bg-border" />
          <span className="overline text-muted-foreground">Or</span>
          <div className="flex-1 h-px bg-border" />
        </div>

        <button onClick={googleLogin} data-testid="google-login" className="btn-outline justify-center">
          Continue with Google
        </button>

        <p className="mt-10 text-sm text-muted-foreground">
          No account yet?{" "}
          <Link to="/register" className="text-foreground border-b border-foreground/40 hover:border-foreground" data-testid="register-link">Create one</Link>
        </p>
      </div>
    </div>
  );
}
