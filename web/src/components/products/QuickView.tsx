import { ExternalLink, Store, Clock, Crown, Wine, MapPin, ShoppingCart } from "lucide-react";
import { Product } from "@/types";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useNavigate } from "react-router-dom";
import {
  formatPromoEndDate,
  formatDistanceAway,
  getDistanceColorClass,
  calculateSavingsPercent,
} from "@/lib/formatters";

interface QuickViewProps {
  product: Product | null;
  isOpen: boolean;
  onClose: () => void;
  isComparing: boolean;
  onToggleCompare: () => void;
  isCompareAtLimit: boolean;
}

export const QuickView = ({
  product,
  isOpen,
  onClose,
  isComparing,
  onToggleCompare,
  isCompareAtLimit,
}: QuickViewProps) => {
  const navigate = useNavigate();

  if (!product) return null;

  const hasPromo = product.price.promo_price_nzd && product.price.promo_price_nzd < product.price.price_nzd;
  const currentPrice = product.price.promo_price_nzd ?? product.price.price_nzd;
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const distanceText = formatDistanceAway(product.price.distance_km);
  const distanceColorClass = getDistanceColorClass(product.price.distance_km);

  const handleViewDetails = () => {
    onClose();
    navigate(`/product/${product.id}`);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px] p-0 overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-0">
          {/* Image Section */}
          <div className="md:col-span-2 bg-white p-6 flex items-center justify-center relative">
            {hasPromo && (
              <div className="absolute top-3 left-3 z-10">
                <Badge className="bg-primary text-white font-semibold text-xs">
                  SALE
                </Badge>
              </div>
            )}
            {hasPromo && savingsPercent > 0 && (
              <div className="absolute top-3 right-3 z-10">
                <Badge className="bg-primary text-white font-semibold text-xs">
                  {savingsPercent}% off
                </Badge>
              </div>
            )}
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-64 object-contain"
              />
            ) : (
              <Wine className="h-32 w-32 text-tertiary-gray/30" />
            )}
          </div>

          {/* Content Section */}
          <div className="md:col-span-3 p-6 flex flex-col">
            {/* Header */}
            <div className="mb-4">
              <h2 className="text-2xl font-bold text-primary-gray mb-2 line-clamp-2">
                {product.name}
              </h2>
              {product.brand && (
                <p className="text-base text-secondary-gray">{product.brand}</p>
              )}
            </div>

            {/* Price */}
            <div className="mb-4">
              <div className="flex items-baseline gap-3 mb-2">
                <span className="text-4xl font-black text-primary">
                  ${currentPrice.toFixed(2)}
                </span>
                {hasPromo && (
                  <span className="text-lg line-through text-tertiary-gray">
                    ${product.price.price_nzd.toFixed(2)}
                  </span>
                )}
              </div>

              {/* Price metrics */}
              <div className="flex flex-wrap gap-2 text-sm text-secondary-gray">
                {product.price.price_per_100ml && (
                  <span>${product.price.price_per_100ml.toFixed(2)} per 100ml</span>
                )}
                {product.price.price_per_standard_drink && (
                  <span>• ${product.price.price_per_standard_drink.toFixed(2)} per drink</span>
                )}
              </div>
            </div>

            {/* Promo badges */}
            {hasPromo && (
              <div className="flex flex-wrap gap-2 mb-4">
                {product.price.is_member_only && (
                  <Badge variant="outline" className="gap-1 text-gold border-gold">
                    <Crown className="h-3 w-3" />
                    Members Only
                  </Badge>
                )}
                {promoEndText && (
                  <Badge variant="outline" className="gap-1 text-primary border-primary/30">
                    <Clock className="h-3 w-3" />
                    {promoEndText}
                  </Badge>
                )}
              </div>
            )}

            {/* Store Info */}
            <div className="mb-4">
              <div className="flex items-center gap-2 text-secondary-gray mb-2">
                <Store className="h-4 w-4 text-primary" />
                <span className="font-medium text-primary-gray">{product.price.store_name}</span>
              </div>
              {distanceText && (
                <div className={cn("flex items-center gap-2", distanceColorClass)}>
                  <MapPin className="h-4 w-4" />
                  <span className="text-sm font-medium">{distanceText}</span>
                </div>
              )}
            </div>

            <Separator className="my-4" />

            {/* Product Details */}
            <div className="mb-6 flex-1">
              <h3 className="text-sm font-semibold mb-3 text-primary-gray">Product Details</h3>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                {product.category && (
                  <>
                    <dt className="text-secondary-gray">Category</dt>
                    <dd className="font-medium text-primary-gray capitalize">
                      {product.category.replace('_', ' ')}
                    </dd>
                  </>
                )}
                {product.abv_percent && (
                  <>
                    <dt className="text-secondary-gray">Alcohol %</dt>
                    <dd className="font-medium text-primary-gray">{product.abv_percent}%</dd>
                  </>
                )}
                {product.total_volume_ml && (
                  <>
                    <dt className="text-secondary-gray">Volume</dt>
                    <dd className="font-medium text-primary-gray">{product.total_volume_ml}ml</dd>
                  </>
                )}
                {product.pack_count && product.pack_count > 1 && (
                  <>
                    <dt className="text-secondary-gray">Pack Size</dt>
                    <dd className="font-medium text-primary-gray">{product.pack_count} units</dd>
                  </>
                )}
              </dl>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant={isComparing ? "default" : "outline"}
                onClick={onToggleCompare}
                disabled={!isComparing && isCompareAtLimit}
                className="flex-1"
              >
                <ShoppingCart className="mr-2 h-4 w-4" />
                {isComparing ? "Remove" : "Compare"}
              </Button>
              {product.product_url && (
                <Button asChild className="flex-1 bg-primary hover:bg-accent">
                  <a
                    href={product.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2"
                  >
                    View at Store
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              )}
            </div>

            <Button
              variant="ghost"
              onClick={handleViewDetails}
              className="w-full mt-2 text-primary hover:text-accent"
            >
              View Full Details
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
