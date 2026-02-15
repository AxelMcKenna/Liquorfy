import { memo, useState } from "react";
import { Store, Clock, Crown, Wine, MapPin, Eye } from "lucide-react";
import { Product } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { QuickView } from "./QuickView";
import {
  formatPromoEndDate,
  formatDistance,
  getDistanceColorClass,
  calculateSavingsPercent,
} from "@/lib/formatters";

interface ProductCardProps {
  product: Product;
  index: number;
}

const ProductCardComponent = ({
  product,
  index,
}: ProductCardProps) => {
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);
  const [showQuickView, setShowQuickView] = useState(false);
  const hasPromo = product.price.promo_price_nzd &&
    product.price.promo_price_nzd < product.price.price_nzd;

  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const distanceText = formatDistance(product.price.distance_km);
  const distanceColorClass = getDistanceColorClass(product.price.distance_km);

  const handleCardClick = () => {
    navigate(`/product/${product.id}`);
  };

  return (
    <Card
      className="h-full flex flex-col overflow-hidden border bg-card hover:shadow-sm transition-shadow cursor-pointer group"
      onClick={handleCardClick}
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
          <Badge className="absolute top-2 left-2 bg-primary text-white text-xs">
            {savingsPercent}% off
          </Badge>
        )}

        {/* Quick View button */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <Button
            size="sm"
            variant="secondary"
            onClick={(e) => {
              e.stopPropagation();
              setShowQuickView(true);
            }}
          >
            <Eye className="mr-1.5 h-4 w-4" />
            Quick View
          </Button>
        </div>
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
        <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
          <span className="flex items-center gap-1">
            <Store className="h-3 w-3" />
            {product.price.store_name}
          </span>
          {distanceText && (
            <span className={cn("flex items-center gap-1", distanceColorClass)}>
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

      {/* Quick View Modal */}
      <QuickView
        product={product}
        isOpen={showQuickView}
        onClose={() => setShowQuickView(false)}
      />
    </Card>
  );
};

export const ProductCard = memo(ProductCardComponent, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.index === nextProps.index
  );
});
