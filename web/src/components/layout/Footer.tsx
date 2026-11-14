import { Link } from 'react-router-dom';

export const Footer = () => {
  return (
    <footer className="border-t bg-secondary/50">
      <div className="max-w-6xl mx-auto px-4 py-6 flex flex-wrap items-center justify-between gap-4 text-xs text-muted-foreground">
        <div>
          <span>&copy; {new Date().getFullYear()} Liquorfy</span>
          <p className="mt-1">Created by <Link to="/about" className="hover:text-foreground transition-colors">Axel McKenna</Link></p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap items-center gap-3">
          <Link to="/about" className="hover:text-foreground transition-colors">About</Link>
          <span aria-hidden="true">&middot;</span>
          <Link to="/terms" className="hover:text-foreground transition-colors">Terms</Link>
          <span>&middot;</span>
          <Link to="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
          <span>&middot;</span>
          <Link to="/support" className="hover:text-foreground transition-colors">Support</Link>
        </nav>
      </div>
    </footer>
  );
};
