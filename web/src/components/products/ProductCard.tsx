import { memo, useState } from "react";
import { Store, Clock, Crown, Wine, MapPin, Eye, Sparkles } from "lucide-react";
import { Product } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { QuickView } from "./QuickView";
import { FavouriteButton } from "./FavouriteButton";
import {
  formatPromoEndDate,
  formatDistance,
  getDistanceColorClass,
  calculateSavingsPercent,
} from "@/lib/formatters";

interface ProductCardProps {
  product: Product;
  index: number;
  isFavourite?: boolean;
  onToggleFavourite?: () => void;
  onView?: () => void;
}

const ProductCardComponent = ({
  product,
  index,
  isFavourite = false,
  onToggleFavourite,
  onView,
}: ProductCardProps) => {
  const [imageError, setImageError] = useState(false);
  const [showQuickView, setShowQuickView] = useState(false);
  const hasPromo = product.price.promo_price_nzd &&
    product.price.promo_price_nzd < product.price.price_nzd;

  const isNewPromo = hasPromo && product.last_updated &&
    (Date.now() - new Date(product.last_updated).getTime()) < 24 * 60 * 60 * 1000;
  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const distanceText = formatDistance(product.price.distance_km);
  const distanceColorClass = getDistanceColorClass(product.price.distance_km);

  const handleCardClick = () => {
    onView?.();
    setShowQuickView(true);
  };

  return (
    <>
      <Card
        className="h-full flex flex-col overflow-hidden border-0 shadow-sm hover:shadow-md transition-shadow cursor-pointer group [backface-visibility:hidden] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 animate-card-enter rounded-xl"
        style={{ animationDelay: `${Math.min(index * 50, 500)}ms` }}
        onClick={handleCardClick}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleCardClick(); } }}
        tabIndex={0}
        role="button"
        aria-label={`View ${product.name}, $${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)} at ${product.price.store_name}`}
      >
        {/* Product Image */}
        <div className="w-full aspect-square relative overflow-hidden bg-white">
          {product.image_url && !imageError ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain p-4 drop-shadow-sm"
              loading="lazy"
              decoding="async"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Wine className="h-12 w-12 text-muted-foreground/20" />
            </div>
          )}

          {/* Sale badges */}
          {hasPromo && savingsPercent > 0 && (
            <div className="absolute top-2 left-2 flex flex-col gap-1 z-10">
              <Badge className="bg-primary text-white text-xs font-semibold shadow-sm">
                {savingsPercent}% off
              </Badge>
              {isNewPromo && (
                <Badge className="bg-amber-500 text-white text-xs gap-1 shadow-sm">
                  <Sparkles className="h-3 w-3" />
                  New
                </Badge>
              )}
            </div>
          )}

          {/* Favourite button */}
          {onToggleFavourite && (
            <div className="absolute top-2 right-2 z-10">
              <FavouriteButton
                isFavourite={isFavourite}
                onToggle={onToggleFavourite}
                className="bg-white/80 backdrop-blur-sm hover:bg-white shadow-sm"
              />
            </div>
          )}

          {/* Quick View button */}
          <div className="absolute inset-0 hidden items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 sm:flex">
            <Button
              size="sm"
              variant="secondary"
              onClick={(e) => {
                e.stopPropagation();
                onView?.();
                setShowQuickView(true);
              }}
            >
              <Eye className="mr-1.5 h-4 w-4" />
              Quick View
            </Button>
          </div>
          <Button
            size="sm"
            variant="secondary"
            className="absolute bottom-2 right-2 sm:hidden"
            onClick={(e) => {
              e.stopPropagation();
              onView?.();
              setShowQuickView(true);
            }}
          >
            <Eye className="mr-1.5 h-4 w-4" />
            Quick View
          </Button>
        </div>

        <CardContent className="p-3 flex-1 bg-[hsl(var(--background))]">
          {/* Product info */}
          <div className="mb-2">
            <h3 className="text-sm font-serif font-semibold line-clamp-2 group-hover:text-primary transition-colors leading-snug">
              {product.name}
            </h3>
            {product.brand && (
              <p className="text-xs text-[hsl(var(--foreground-secondary))] mt-0.5">
                {product.brand}
              </p>
            )}
          </div>

          {/* Store & distance */}
          <div className="flex items-center justify-between text-xs text-[hsl(var(--foreground-secondary))] mb-2">
            <span className="flex items-center gap-1 min-w-0 truncate">
              <Store className="h-3 w-3 text-primary flex-shrink-0" />
              <span className="truncate">{product.price.store_name}</span>
            </span>
            {distanceText && (
              <span className={cn("flex items-center gap-1 flex-shrink-0 ml-2 font-medium", distanceColorClass)}>
                <MapPin className="h-3 w-3" />
                {distanceText}
              </span>
            )}
          </div>

          {/* Price */}
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-primary tracking-tight">
              ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
            </span>
            {hasPromo && (
              <span className="text-xs line-through text-[hsl(var(--foreground-tertiary))]">
                ${product.price.price_nzd.toFixed(2)}
              </span>
            )}
          </div>

          {/* Badges */}
          {hasPromo && (product.price.is_member_only || promoEndText) && (
            <div className="flex flex-wrap gap-1 mt-2">
              {product.price.is_member_only && (
                <Badge variant="outline" className="text-xs gap-1 text-gold border-gold font-medium">
                  <Crown className="h-3 w-3" />
                  Members
                </Badge>
              )}
              {promoEndText && (
                <Badge variant="outline" className="text-xs gap-1 text-primary border-primary/30 font-medium">
                  <Clock className="h-3 w-3" />
                  {promoEndText}
                </Badge>
              )}
            </div>
          )}

          {/* Per unit price */}
          {product.price.price_per_100ml && (
            <p className="text-xs text-[hsl(var(--foreground-secondary))] mt-2">
              ${product.price.price_per_100ml.toFixed(2)} / 100ml
            </p>
          )}
        </CardContent>
      </Card>

      <QuickView
        product={product}
        isOpen={showQuickView}
        onClose={() => setShowQuickView(false)}
        isFavourite={isFavourite}
        onToggleFavourite={onToggleFavourite}
      />
    </>
  );
};

export const ProductCard = memo(ProductCardComponent, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.index === nextProps.index &&
    prevProps.isFavourite === nextProps.isFavourite
  );
});
