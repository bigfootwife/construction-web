import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-muted mt-32" data-testid="site-footer">
      <div className="container-x py-20 grid grid-cols-1 md:grid-cols-12 gap-12">
        <div className="md:col-span-5">
          <div className="flex items-center gap-2 mb-6">
            <span className="w-2 h-2 bg-primary"></span>
            <span className="font-display text-xl tracking-tight font-medium">STONEBRIDGE</span>
          </div>
          <p className="text-base text-muted-foreground max-w-md leading-relaxed">
            A construction studio building residential, commercial, and renovation projects
            with editorial precision since 1998.
          </p>
          <div className="mt-10 overline">Get in touch</div>
          <a href="mailto:hello@stonebridge.com" className="font-display text-3xl lg:text-4xl mt-3 inline-block hover:text-primary transition-colors">
            hello@stonebridge.com
          </a>
        </div>

        <div className="md:col-span-3">
          <div className="overline mb-5">Studio</div>
          <ul className="space-y-3 text-sm">
            <li><Link to="/about" className="hover:text-primary">About us</Link></li>
            <li><Link to="/portfolio" className="hover:text-primary">Selected Work</Link></li>
            <li><Link to="/services" className="hover:text-primary">Services</Link></li>
            <li><Link to="/contact" className="hover:text-primary">Inquire</Link></li>
          </ul>
        </div>

        <div className="md:col-span-2">
          <div className="overline mb-5">Visit</div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            1842 Larimer St<br/>
            Floor 4<br/>
            Denver, CO 80202
          </p>
        </div>

        <div className="md:col-span-2">
          <div className="overline mb-5">Follow</div>
          <ul className="space-y-3 text-sm">
            <li><a href="#" className="hover:text-primary">Instagram</a></li>
            <li><a href="#" className="hover:text-primary">LinkedIn</a></li>
            <li><a href="#" className="hover:text-primary">Pinterest</a></li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border/60">
        <div className="container-x py-6 flex flex-col md:flex-row md:justify-between gap-3 text-xs text-muted-foreground">
          <span>© {new Date().getFullYear()} Stonebridge Construction Co.</span>
          <span className="uppercase tracking-[0.2em]">Built for makers · Licensed · Insured</span>
        </div>
      </div>
    </footer>
  );
}
