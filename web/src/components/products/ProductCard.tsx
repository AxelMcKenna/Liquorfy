import { memo, useState } from "react";
import { motion } from "framer-motion";
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
  if (diffDays <= 7) return `Ends in ${diffDays} days`;

  // Format as "Ends Dec 31"
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02, duration: 0.4 }}
      className="h-full"
    >
      <Card
        className="glass-card-hover h-full flex flex-col overflow-hidden relative group cursor-pointer"
        onClick={handleCardClick}
      >
        {/* Promo ribbon */}
        {hasPromo && (
          <div className="absolute top-3 -left-2 z-20">
            <div className="promo-badge transform -rotate-2 rounded">
              SALE
            </div>
          </div>
        )}

        {/* Savings percentage badge */}
        {hasPromo && savingsPercent > 0 && (
          <div className="absolute top-3 right-3 z-20">
            <Badge className="bg-green-600 text-white font-bold text-xs px-2 py-1 shadow-md">
              Save {savingsPercent}%
            </Badge>
          </div>
        )}

        {/* Product Image */}
        <div className="w-full aspect-square sm:aspect-[0.8/1] bg-white relative overflow-hidden group/image">
          {product.image_url && !imageError ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-contain p-3"
              loading="lazy"
              decoding="async"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-tertiary to-secondary">
              <Wine className="h-16 w-16 text-tertiary-gray/30" />
            </div>
          )}

          {/* Quick View button - shows on hover */}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover/image:opacity-100 transition-opacity flex items-center justify-center">
            <Button
              onClick={(e) => {
                e.stopPropagation();
                setShowQuickView(true);
              }}
              className="bg-white text-primary hover:bg-white/90 shadow-lg"
            >
              <Eye className="mr-2 h-4 w-4" />
              Quick View
            </Button>
          </div>
        </div>

        <CardContent className="p-4 flex-1">
          {/* Product info */}
          <div className="mb-3">
            <h3 className="text-sm font-semibold line-clamp-2 group-hover:text-primary transition-colors text-primary-gray tracking-tight">
              {product.name}
            </h3>
            <p className="text-xs mt-1 text-tertiary-gray">
              {product.brand ?? "Unknown brand"}
            </p>
            <div className="flex items-center gap-1 mt-1">
              <Store className="h-3 w-3 text-primary" />
              <p className="text-xs text-tertiary-gray">{product.price.store_name}</p>
            </div>
            {product.price.distance_km !== null && product.price.distance_km !== undefined && (
              <div className="flex items-center gap-1 mt-1">
                <MapPin className={`h-3 w-3 ${
                  product.price.distance_km < 2 ? 'text-green-600' :
                  product.price.distance_km < 5 ? 'text-yellow-600' :
                  'text-gray-400'
                }`} />
                <p className={`text-xs font-medium ${
                  product.price.distance_km < 2 ? 'text-green-600' :
                  product.price.distance_km < 5 ? 'text-yellow-600' :
                  'text-tertiary-gray'
                }`}>
                  {product.price.distance_km < 1
                    ? `${Math.round(product.price.distance_km * 1000)}m away`
                    : `${product.price.distance_km.toFixed(1)}km away`}
                </p>
              </div>
            )}
          </div>

          {/* Price display */}
          <div className="space-y-2">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-semibold text-primary">
                ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
              </span>
              {hasPromo && (
                <span className="text-xs line-through text-tertiary-gray">
                  ${product.price.price_nzd.toFixed(2)}
                </span>
              )}
            </div>

            {/* Promo badges */}
            {hasPromo && (
              <div className="flex flex-wrap gap-1">
                {product.price.is_member_only && (
                  <Badge variant="secondary" className="text-xs gap-1 bg-gold/20 text-gold border-gold/30 rounded-md">
                    <Crown className="h-3 w-3" />
                    Members
                  </Badge>
                )}
                {promoEndText && (
                  <Badge variant="outline" className="text-xs gap-1 text-primary rounded-md border-primary/30">
                    <Clock className="h-3 w-3" />
                    {promoEndText}
                  </Badge>
                )}
              </div>
            )}

            {/* Value metrics */}
            {product.price.price_per_100ml && (
              <p className="text-xs text-tertiary-gray">
                ${product.price.price_per_100ml.toFixed(2)} per 100ml
              </p>
            )}
          </div>
        </CardContent>

        <CardFooter className="p-4 pt-0">
          <Button
            variant={isComparing ? "default" : "outline"}
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
            size="sm"
            disabled={!isComparing && isCompareAtLimit}
            className={cn(
              "w-full font-medium transition-all rounded-card-xl",
              isComparing
                ? "bg-primary hover:bg-accent"
                : "hover:bg-gray-50 border-subtle"
            )}
            title={!isComparing && isCompareAtLimit ? "Maximum 4 products can be compared" : undefined}
          >
            <ShoppingCart className="mr-2 h-3 w-3" />
            {isComparing ? "Remove" : "Compare"}
          </Button>
        </CardFooter>
      </Card>

      {/* Quick View Modal */}
      <QuickView
        product={product}
        isOpen={showQuickView}
        onClose={() => setShowQuickView(false)}
        isComparing={isComparing}
        onToggleCompare={onToggleCompare}
        isCompareAtLimit={isCompareAtLimit}
      />
    </motion.div>
  );
};

// Memoize the component to prevent unnecessary re-renders
export const ProductCard = memo(ProductCardComponent, (prevProps, nextProps) => {
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.isComparing === nextProps.isComparing &&
    prevProps.index === nextProps.index
  );
});
