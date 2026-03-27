import { ReactNode } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

interface PageHeaderProps {
  /** Content rendered on the right side of the header */
  rightContent?: ReactNode;
  /** If true, back button navigates to browser history (-1). Otherwise links to "/" */
  backTo?: string | "history";
  /** Make header sticky */
  sticky?: boolean;
}

export const PageHeader = ({
  rightContent,
  backTo = "history",
  sticky = false,
}: PageHeaderProps) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleBack = () => {
    if (backTo !== "history") {
      navigate(backTo);
    } else if (location.key !== "default") {
      // Browser has real history to go back to
      navigate(-1);
    } else {
      // Direct URL visit — no history, fall back to explore
      navigate("/explore");
    }
  };

  return (
    <header className={`bg-primary border-b border-primary ${sticky ? "sticky top-0 z-50" : ""}`}>
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <button
          onClick={handleBack}
          className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white transition-colors min-w-[60px]"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Back</span>
        </button>
        <Link to="/" className="text-lg font-semibold text-white uppercase tracking-[0.15em] font-sans">
          LIQUORFY
        </Link>
        <div className="flex items-center gap-1 min-w-[60px] justify-end">
          {rightContent}
        </div>
      </div>
    </header>
  );
};
