import { memo, useState } from "react";
import { Link } from "react-router-dom";
import { Store, Clock, Crown, Wine, MapPin, TrendingDown } from "lucide-react";
import { Product, SortOption } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { FavouriteButton } from "./FavouriteButton";
import {
  formatPromoEndDate,
  formatDistance,
  getDistanceColorClass,
  calculateSavingsPercent,
  calculateSavingsAmount,
} from "@/lib/formatters";

interface ProductCardProps {
  product: Product;
  index: number;
  sort?: SortOption;
  isFavourite?: boolean;
  onToggleFavourite?: () => void;
  onView?: () => void;
}

const ProductCardComponent = ({
  product,
  index,
  sort = SortOption.BEST_VALUE,
  isFavourite = false,
  onToggleFavourite,
  onView,
}: ProductCardProps) => {
  const [imageError, setImageError] = useState(false);
  const hasPromo = product.price.promo_price_nzd &&
    product.price.promo_price_nzd < product.price.price_nzd;

  const isNewPromo = hasPromo && product.last_updated &&
    (Date.now() - new Date(product.last_updated).getTime()) < 24 * 60 * 60 * 1000;
  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const savingsAmount = calculateSavingsAmount(product.price.price_nzd, product.price.promo_price_nzd);
  const distanceText = formatDistance(product.price.distance_km);
  const distanceColorClass = getDistanceColorClass(product.price.distance_km);

  return (
    <Card
      variant="interactive"
      className="relative h-full overflow-hidden group [backface-visibility:hidden] animate-card-enter"
      style={{ animationDelay: `${Math.min(index * 50, 500)}ms` }}
    >
      <Link
        to={`/product/${product.id}`}
        onClick={onView}
        className="flex h-full flex-col rounded-[inherit] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset"
        aria-label={`View details for ${product.name}, $${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}${product.is_cheapest_nearby ? ', cheapest nearby' : ''} at ${product.price.store_name}`}
      >
        {/* Product Image */}
        <div className="w-full aspect-[4/3] sm:aspect-square relative overflow-hidden border-b border-border/60 bg-white">
          {product.image_url && !imageError ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain p-3 sm:p-4 transition-transform duration-300 group-hover:scale-[1.03]"
              loading="lazy"
              decoding="async"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Wine className="h-10 w-10 sm:h-12 sm:w-12 text-muted-foreground/20" />
            </div>
          )}

          {/* Sale badge */}
          {hasPromo && savingsPercent > 0 && (
            <div className="absolute top-2 left-2 flex gap-1">
              <Badge className="bg-primary text-white text-xs shadow-sm">
                {savingsPercent}% off
              </Badge>
              {isNewPromo && (
                <Badge className="bg-amber-500 text-white text-xs shadow-sm">
                  New
                </Badge>
              )}
            </div>
          )}
        </div>

        <CardContent className="p-3 flex-1">
          {/* Product info */}
          <div className="mb-2">
            <h3 className="min-h-10 text-[13px] sm:text-sm font-medium leading-5 line-clamp-2 group-hover:text-primary transition-colors">
              {product.name}
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5 truncate">
              {product.brand ?? "Brand unavailable"}
            </p>
          </div>

          {/* Store info */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2 min-w-0">
            <span className="flex items-center gap-1 min-w-0 truncate" title={product.price.store_name}>
              <Store className="h-3 w-3 flex-shrink-0" />
              <span className="truncate">{product.price.store_name}</span>
            </span>
            {distanceText && (
              <span className={cn(
                "flex items-center gap-0.5 flex-shrink-0 rounded-full bg-secondary px-1.5 py-0.5 font-medium",
                distanceColorClass
              )}>
                <MapPin className="h-3 w-3" />
                {distanceText}
              </span>
            )}
          </div>

          {/* Cheapest-nearby trust signal */}
          {product.is_cheapest_nearby && (
            <div className="flex items-center gap-1 text-xs font-semibold text-primary mb-1">
              <TrendingDown className="h-3 w-3 flex-shrink-0" />
              Cheapest nearby
            </div>
          )}

          {/* Price */}
          <div className="flex items-baseline gap-1.5 sm:gap-2">
            <span className="text-lg sm:text-xl font-semibold tracking-tight tabular-nums text-primary">
              ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
            </span>
            {hasPromo && (
              <span className="text-xs line-through text-muted-foreground">
                ${product.price.price_nzd.toFixed(2)}
              </span>
            )}
          </div>

          {/* Savings - the tangible value, in dollars */}
          {hasPromo && savingsAmount > 0 && (
            <p className="text-xs font-semibold text-primary mt-0.5">
              Save ${savingsAmount.toFixed(2)}
            </p>
          )}

          {/* Badges */}
          {hasPromo && (
            <div className="flex flex-wrap gap-1 mt-2">
              {product.price.is_member_only && (
                <>
                  <Badge variant="outline" className="text-xs gap-0 px-1.5 sm:hidden" title="Members only">
                    <Crown className="h-3 w-3" />
                  </Badge>
                  <Badge variant="outline" className="text-xs gap-1 hidden sm:inline-flex">
                    <Crown className="h-3 w-3" />
                    Members
                  </Badge>
                </>
              )}
              {promoEndText && (
                <Badge variant="outline" className="text-xs gap-1 hidden sm:inline-flex">
                  <Clock className="h-3 w-3" />
                  {promoEndText}
                </Badge>
              )}
            </div>
          )}

          {/* Per-unit price matching the active sort */}
          {sort === SortOption.BEST_PER_DRINK
            ? product.price.price_per_standard_drink != null && (
                <p className="text-xs text-muted-foreground mt-2">
                  ${product.price.price_per_standard_drink.toFixed(2)} / std drink
                </p>
              )
            : product.price.price_per_100ml != null && (
                <p className="text-xs text-muted-foreground mt-2">
                  ${product.price.price_per_100ml.toFixed(2)} / 100ml
                </p>
              )}
        </CardContent>
      </Link>

      {onToggleFavourite && (
        <div className="absolute top-2 right-2 z-10">
          <FavouriteButton
            isFavourite={isFavourite}
            onToggle={onToggleFavourite}
            className="bg-white/90 backdrop-blur-sm hover:bg-white shadow-sm"
          />
        </div>
      )}
    </Card>
  );
};

export const ProductCard = memo(ProductCardComponent);
