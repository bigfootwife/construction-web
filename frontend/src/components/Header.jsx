import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Menu, X } from "lucide-react";
import { useState } from "react";

const links = [
  { to: "/", label: "Home" },
  { to: "/services", label: "Services" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/about", label: "About" },
  { to: "/contact", label: "Contact" },
];

export default function Header() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header
      className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border/60"
      data-testid="site-header"
    >
      <div className="container-x flex items-center justify-between h-20">
        <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
          <span className="w-2 h-2 bg-primary"></span>
          <span className="font-display text-xl tracking-tight font-medium">
            STONEBRIDGE
          </span>
          <span className="hidden sm:inline text-[10px] uppercase tracking-[0.25em] text-muted-foreground ml-2 border-l border-border pl-2">
            Est. 1998
          </span>
        </Link>

        <nav className="hidden lg:flex items-center gap-10">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              data-testid={`nav-${l.label.toLowerCase()}`}
              className={({ isActive }) =>
                `text-xs font-semibold uppercase tracking-[0.18em] transition-colors ${
                  isActive ? "text-primary" : "text-foreground hover:text-primary"
                }`
              }
              end={l.to === "/"}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden lg:flex items-center gap-4">
          {user ? (
            <Link to="/dashboard" data-testid="dashboard-link" className="btn-outline">
              Dashboard
            </Link>
          ) : (
            <Link to="/login" data-testid="login-link" className="btn-outline">
              Client Login
            </Link>
          )}
        </div>

        <button
          className="lg:hidden p-2"
          onClick={() => setOpen((s) => !s)}
          data-testid="mobile-menu-toggle"
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>

      {open && (
        <div className="lg:hidden border-t border-border bg-background">
          <div className="container-x py-6 flex flex-col gap-5">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                onClick={() => setOpen(false)}
                className="text-sm font-semibold uppercase tracking-[0.18em]"
                data-testid={`mobile-nav-${l.label.toLowerCase()}`}
              >
                {l.label}
              </NavLink>
            ))}
            <Link
              to={user ? "/dashboard" : "/login"}
              onClick={() => setOpen(false)}
              className="btn-outline self-start"
              data-testid="mobile-dashboard-link"
            >
              {user ? "Dashboard" : "Client Login"}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
