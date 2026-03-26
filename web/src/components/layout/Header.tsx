import { MapPin, User } from "lucide-react";
import { Link } from "react-router-dom";
import { useLocationContext } from "@/contexts/LocationContext";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { UserMenu } from "@/components/auth/UserMenu";
import { SearchAutocomplete } from "@/components/search/SearchAutocomplete";

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
                <Button size="sm" className="text-white hover:bg-white/10 font-semibold gap-2">
                  <User className="h-4 w-4" />
                  Account
                </Button>
              </Link>
            )}
          </div>
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-semibold text-white mb-2 tracking-[0.15em] font-sans">
              LIQUORFY
            </h1>
            <p className="text-sm text-white/80 mb-6">
              Compare liquor prices across NZ
            </p>
            <SearchAutocomplete
              query={query}
              setQuery={setQuery}
              onSearch={onSearch}
              placeholder="Search for beer, wine, spirits..."
              className="max-w-xl mx-auto"
              inputClassName="h-12 bg-white text-base"
            />
          </div>
        </div>
      </header>
    );
  }

  return (
    <header className="bg-primary border-b border-primary">
      <div className="px-4 py-3">
        {/* Mobile: logo row + search row */}
        <div className="flex items-center justify-between gap-2 sm:hidden">
          <Link to="/" className="flex-shrink-0">
            <span className="text-lg font-semibold text-white tracking-[0.15em] font-sans">LIQUORFY</span>
          </Link>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={openLocationModal}
              className="text-white hover:bg-white/10 h-8 w-8 focus-visible:ring-0 focus-visible:ring-offset-0"
            >
              <MapPin className="h-4 w-4" />
            </Button>
            {user ? (
              <UserMenu />
            ) : (
              <Link to="/login">
                <Button size="icon" className="text-white hover:bg-white/10 h-8 w-8">
                  <User className="h-4 w-4" />
                </Button>
              </Link>
            )}
          </div>
        </div>
        <div className="mt-2 sm:hidden">
          <SearchAutocomplete
            query={query}
            setQuery={setQuery}
            onSearch={onSearch}
            className="w-full"
            inputClassName="h-10 bg-white text-sm"
          />
        </div>

        {/* Desktop: 3-column grid */}
        <div className="hidden sm:grid grid-cols-3 items-center gap-4">
          {/* Logo - left */}
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0">
              <span className="text-xl font-semibold text-white tracking-[0.15em] font-sans">LIQUORFY</span>
            </Link>
          </div>

          {/* Search - centered */}
          <div className="flex justify-center">
            <SearchAutocomplete
              query={query}
              setQuery={setQuery}
              onSearch={onSearch}
              className="w-full max-w-md"
              inputClassName="h-10 bg-white text-sm"
            />
          </div>

          {/* Right side - location + account */}
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={openLocationModal}
              className="text-white hover:bg-white/10 gap-2 focus-visible:ring-0 focus-visible:ring-offset-0"
            >
              <MapPin className="h-4 w-4" />
              <span>
                {isLocationSet ? `${radiusKm} km` : 'Location'}
              </span>
            </Button>
            {user ? (
              <UserMenu />
            ) : (
              <Link to="/login">
                <Button size="sm" className="text-white hover:bg-white/10 font-semibold gap-2">
                  <User className="h-4 w-4" />
                  <span>Account</span>
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
