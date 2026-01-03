import { motion } from "framer-motion";
import { Search, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { useLocationContext } from "@/contexts/LocationContext";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

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

  if (variant === 'landing') {
    return (
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-primary border-b-4 border-primary"
      >
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 }}
            >
              <h1 className="text-4xl md:text-6xl font-black text-white mb-2" style={{ letterSpacing: '0.1em' }}>
                LIQUORFY
              </h1>
              <p className="text-lg text-white/90 font-medium mb-8">
                Cheapest liquor in Aotearoa
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="max-w-3xl mx-auto"
            >
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-6 w-6 text-muted-foreground" />
                <Input
                  placeholder="Search for beer, wine, spirits..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && onSearch()}
                  className="pl-14 pr-4 py-8 bg-white text-lg font-medium shadow-lg"
                />
              </div>
            </motion.div>
          </div>
        </div>
      </motion.header>
    );
  }

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#0e3f2c] border-b border-[#0e3f2c]"
    >
      <div className="max-w-7xl mx-auto pl-0 pr-4 py-7">
        <div className="flex flex-col md:grid md:grid-cols-[auto,1fr,auto] md:items-center gap-4">
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex-shrink-0 -ml-6 sm:-ml-8 lg:-ml-14"
          >
            <Link to="/" className="block group">
              <h1 className="text-4xl font-semibold group-hover:text-white/80 transition-colors text-white tracking-tight">
                LIQUORFY
              </h1>
              <p className="text-sm hidden md:block text-white/80">
                Cheapest liquor in Aotearoa
              </p>
            </Link>
          </motion.div>

          {/* Search */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full md:w-full md:max-w-2xl md:justify-self-center"
          >
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-500" />
              <Input
                placeholder="Search for products..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && onSearch()}
                className="pl-12 pr-4 py-7 rounded-card-xl border-transparent bg-white text-foreground text-base"
              />
            </div>
          </motion.div>

          {/* Location button */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="-mr-6 sm:-mr-8 lg:-mr-14 md:justify-self-end"
          >
            <Button
              variant="outline"
              onClick={openLocationModal}
              className="flex items-center gap-2 rounded-card-xl font-medium border-white/40 text-white py-7 px-6 hover:bg-white/10 text-base"
            >
              <MapPin className="h-4 w-4 text-white" />
              <span>{isLocationSet ? `Search Radius · ${radiusKm} km` : 'Set Location'}</span>
            </Button>
          </motion.div>
        </div>
      </div>
    </motion.header>
  );
};
