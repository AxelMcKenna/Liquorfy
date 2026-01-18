import { memo, useState } from "react";
import { ShoppingCart, Store, Clock, Crown, Wine, MapPin, Eye } from "lucide-react";
import { Product } from "@/types";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { QuickView } from "./QuickView";

interface ProductCardProps {
  product: Product;
  isComparing: boolean;
  onToggleCompare: () => void;
  index: number;
  isCompareAtLimit?: boolean;
}

const formatPromoEndDate = (endDate: string | null | undefined): string | null => {
  if (!endDate) return null;

  const end = new Date(endDate);
  const now = new Date();
  const diffTime = end.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return "Expired";
  if (diffDays === 0) return "Ends today";
  if (diffDays === 1) return "Ends tomorrow";
  if (diffDays <= 7) return `${diffDays}d left`;

  return `Ends ${end.toLocaleDateString('en-NZ', { month: 'short', day: 'numeric' })}`;
};

const ProductCardComponent = ({
  product,
  isComparing,
  onToggleCompare,
  index,
  isCompareAtLimit = false,
}: ProductCardProps) => {
  const navigate = useNavigate();
  const [imageError, setImageError] = useState(false);
  const [showQuickView, setShowQuickView] = useState(false);
  const hasPromo = product.price.promo_price_nzd &&
    product.price.promo_price_nzd < product.price.price_nzd;

  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);

  const savingsPercent = hasPromo
    ? Math.round(((product.price.price_nzd - product.price.promo_price_nzd!) / product.price.price_nzd) * 100)
    : 0;

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
          {product.price.distance_km !== null && product.price.distance_km !== undefined && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3 w-3" />
              {product.price.distance_km < 1
                ? `${Math.round(product.price.distance_km * 1000)}m`
                : `${product.price.distance_km.toFixed(1)}km`}
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

      <CardFooter className="p-3 pt-0">
        <Button
          variant={isComparing ? "default" : "outline"}
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onToggleCompare();
            if (!isComparing && !isCompareAtLimit) {
              toast.success("Added to comparison", {
                description: product.name,
                duration: 2000,
              });
            } else if (isComparing) {
              toast.info("Removed from comparison", {
                description: product.name,
                duration: 2000,
              });
            }
          }}
          disabled={!isComparing && isCompareAtLimit}
          className="w-full"
          title={!isComparing && isCompareAtLimit ? "Maximum 4 products can be compared" : undefined}
        >
          <ShoppingCart className="mr-1.5 h-3.5 w-3.5" />
          {isComparing ? "Remove" : "Compare"}
        </Button>
      </CardFooter>

      {/* Quick View Modal */}
      <QuickView
        product={product}
        isOpen={showQuickView}
        onClose={() => setShowQuickView(false)}
        isComparing={isComparing}
        onToggleCompare={onToggleCompare}
        isCompareAtLimit={isCompareAtLimit}
      />
    </Card>
  );
};

export const ProductCard = memo(ProductCardComponent, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.isComparing === nextProps.isComparing &&
    prevProps.index === nextProps.index
  );
});
