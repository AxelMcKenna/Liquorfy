import { Link } from 'react-router-dom';
import { Beer, Wine, Martini, CupSoda, GlassWater, Citrus, type LucideIcon } from 'lucide-react';

interface CategoryTile {
  label: string;
  category: string;
  icon: LucideIcon;
}

const tiles: CategoryTile[] = [
  { label: 'Beer', category: 'beer', icon: Beer },
  { label: 'Wine', category: 'wine', icon: Wine },
  { label: 'Spirits', category: 'spirits', icon: Martini },
  { label: 'RTDs', category: 'rtd', icon: CupSoda },
  { label: 'Cider', category: 'cider', icon: Citrus },
  { label: 'Non-Alcoholic', category: 'non_alcoholic', icon: GlassWater },
];

/** Shown on the landing page when there are no recently-viewed products. */
export const CategoryBrowse = () => {
  return (
    <section className="py-12 border-t">
      <div className="max-w-7xl mx-auto px-4">
        <h2 className="text-xl font-semibold text-foreground mb-6">Browse by category</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {tiles.map((tile) => (
            <Link
              key={tile.category}
              to={`/explore?category=${tile.category}`}
              className="group flex flex-col items-center justify-center gap-3 rounded-xl border bg-background p-6 text-center card-lift"
            >
              <span className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                <tile.icon className="h-6 w-6" />
              </span>
              <span className="text-sm font-medium text-foreground">{tile.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};
