import { Search, MapPin, User } from "lucide-react";
import { Link } from "react-router-dom";
import { useLocationContext } from "@/contexts/LocationContext";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/auth/UserMenu";

interface HeaderProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
  variant?: 'compact' | 'landing';
}

export const Header = ({
  query,
  setQuery,
  onSearch,
  variant = 'compact',
}: HeaderProps) => {
  const { radiusKm, isLocationSet, openLocationModal } = useLocationContext();
  const { user } = useAuth();

  if (variant === 'landing') {
    return (
      <header className="bg-primary border-b border-primary">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Top bar with account */}
          <div className="flex justify-end mb-6">
            {user ? (
              <UserMenu />
            ) : (
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-white hover:bg-white/10 gap-2">
                  <User className="h-4 w-4" />
                  <span>Sign In</span>
                </Button>
              </Link>
            )}
          </div>
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-semibold text-white mb-2 tracking-tight">
              LIQUORFY
            </h1>
            <p className="text-sm text-white/80 mb-6">
              Compare liquor prices across NZ
            </p>
            <div className="max-w-xl mx-auto relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Search for beer, wine, spirits..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
                className="pl-12 h-12 bg-white text-base"
              />
            </div>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-primary border-b border-primary">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between gap-6">
          {/* Logo - hugs left edge */}
          <Link to="/" className="flex-shrink-0">
            <span className="text-lg font-semibold text-white">LIQUORFY</span>
          </Link>

          {/* Search - centered */}
          <div className="flex-1 flex justify-center">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search products..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
                className="pl-10 h-10 bg-white text-sm"
              />
            </div>
          </div>

          {/* Right side - location + auth */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={openLocationModal}
              className="text-white hover:bg-white/10 gap-2"
            >
              <MapPin className="h-4 w-4" />
              <span className="hidden sm:inline">
                {isLocationSet ? `${radiusKm} km` : 'Location'}
              </span>
            </Button>
            {user ? (
              <UserMenu />
            ) : (
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-white hover:bg-white/10 gap-2">
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline">Sign In</span>
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
