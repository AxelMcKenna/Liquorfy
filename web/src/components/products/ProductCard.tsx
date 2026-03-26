import { memo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Store, Clock, Crown, Wine, MapPin } from "lucide-react";
import { Product } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
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
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);
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
    navigate(`/product/${product.id}`);
  };

  return (
    <Card
      className="h-full flex flex-col overflow-hidden border bg-white hover:shadow-sm transition-shadow cursor-pointer group [backface-visibility:hidden] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 animate-card-enter"
      style={{ animationDelay: `${Math.min(index * 50, 500)}ms` }}
      onClick={handleCardClick}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleCardClick(); } }}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${product.name}, $${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)} at ${product.price.store_name}`}
    >
      {/* Product Image */}
      <div className="w-full aspect-square relative overflow-hidden border-b">
        {product.image_url && !imageError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-contain p-4"
            loading="lazy"
            decoding="async"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Wine className="h-12 w-12 text-muted-foreground/20" />
          </div>
        )}

        {/* Sale badge */}
        {hasPromo && savingsPercent > 0 && (
          <div className="absolute top-2 left-2 flex gap-1">
            <Badge className="bg-primary text-white text-xs">
              {savingsPercent}% off
            </Badge>
            {isNewPromo && (
              <Badge className="bg-amber-500 text-white text-xs">
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
      </div>

      <CardContent className="p-3 flex-1">
        {/* Product info */}
        <div className="mb-2">
          <h3 className="text-sm font-medium line-clamp-2 group-hover:text-primary transition-colors">
            {product.name}
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {product.brand ?? "Unknown brand"}
          </p>
        </div>

        {/* Store info */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2 min-w-0">
          <span className="flex items-center gap-1 min-w-0 truncate">
            <Store className="h-3 w-3 flex-shrink-0" />
            <span className="truncate">{product.price.store_name}</span>
          </span>
          {distanceText && (
            <span className={cn("flex items-center gap-1 flex-shrink-0", distanceColorClass)}>
              <MapPin className="h-3 w-3" />
              {distanceText}
            </span>
          )}
        </div>

        {/* Price */}
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-semibold text-primary">
            ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
          </span>
          {hasPromo && (
            <span className="text-xs line-through text-muted-foreground">
              ${product.price.price_nzd.toFixed(2)}
            </span>
          )}
        </div>

        {/* Badges */}
        {hasPromo && (
          <div className="flex flex-wrap gap-1 mt-2">
            {product.price.is_member_only && (
              <Badge variant="outline" className="text-xs gap-1">
                <Crown className="h-3 w-3" />
                Members
              </Badge>
            )}
            {promoEndText && (
              <Badge variant="outline" className="text-xs gap-1">
                <Clock className="h-3 w-3" />
                {promoEndText}
              </Badge>
            )}
          </div>
        )}

        {/* Per unit price */}
        {product.price.price_per_100ml && (
          <p className="text-xs text-muted-foreground mt-2">
            ${product.price.price_per_100ml.toFixed(2)} / 100ml
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export const ProductCard = memo(ProductCardComponent, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.index === nextProps.index &&
    prevProps.isFavourite === nextProps.isFavourite
  );
});
