import { Link } from 'react-router-dom';

export const Footer = () => {
  return (
    <footer className="border-t bg-background">
      <div className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between text-xs text-muted-foreground">
        <span>&copy; {new Date().getFullYear()} Liquorfy</span>
        <div className="flex items-center gap-3">
          <Link to="/terms" className="hover:text-foreground transition-colors">Terms</Link>
          <span>&middot;</span>
          <Link to="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
          <span>&middot;</span>
          <Link to="/support" className="hover:text-foreground transition-colors">Support</Link>
        </div>
      </div>
    </footer>
  );
};
