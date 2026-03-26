import { ExternalLink, Store, Clock, Crown, Wine, MapPin, Sparkles } from "lucide-react";
import { Product } from "@/types";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { FavouriteButton } from "./FavouriteButton";
import { ShareButton } from "./ShareButton";
import { PriceAlertButton } from "@/components/alerts/PriceAlertButton";
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
  isFavourite?: boolean;
  onToggleFavourite?: () => void;
}

export const QuickView = ({
  product,
  isOpen,
  onClose,
  isFavourite = false,
  onToggleFavourite,
}: QuickViewProps) => {
  if (!product) return null;

  const hasPromo = product.price.promo_price_nzd && product.price.promo_price_nzd < product.price.price_nzd;
  const currentPrice = product.price.promo_price_nzd ?? product.price.price_nzd;
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const distanceText = formatDistanceAway(product.price.distance_km);
  const distanceColorClass = getDistanceColorClass(product.price.distance_km);
  const isNewPromo = hasPromo && product.last_updated &&
    (Date.now() - new Date(product.last_updated).getTime()) < 24 * 60 * 60 * 1000;

  const details = [
    product.category && { label: "Category", value: product.category.replace('_', ' ') },
    product.abv_percent && { label: "ABV", value: `${product.abv_percent}%` },
    product.total_volume_ml && { label: "Volume", value: `${product.total_volume_ml}ml` },
    product.pack_count && product.pack_count > 1 && { label: "Pack", value: `${product.pack_count} units` },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-[26rem] p-0 max-h-[90vh] overflow-y-auto rounded-xl border-0 shadow-2xl bg-[hsl(var(--background))]">
        <div className="flex flex-col">

          {/* ── Image Section ── */}
          <div className="relative flex items-center justify-center p-6">
{product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="relative z-10 w-full h-72 object-contain drop-shadow-sm"
              />
            ) : (
              <Wine className="relative z-10 h-24 w-24 text-[hsl(var(--foreground-tertiary))]/30" />
            )}

            {/* Badges pinned top-left */}
            {hasPromo && (
              <div className="absolute top-3 left-3 flex flex-col gap-1.5 z-20">
                {savingsPercent > 0 && (
                  <Badge className="bg-primary text-white font-semibold text-xs shadow-sm">
                    {savingsPercent}% off
                  </Badge>
                )}
                {isNewPromo && (
                  <Badge className="bg-amber-500 text-white text-xs gap-1 shadow-sm">
                    <Sparkles className="h-3 w-3" />
                    New
                  </Badge>
                )}
              </div>
            )}

            {/* Action buttons pinned top-right, below close X */}
            <div className="absolute top-10 right-3 flex items-center gap-1 z-20">
              {onToggleFavourite && (
                <FavouriteButton
                  isFavourite={isFavourite}
                  onToggle={onToggleFavourite}
                  className="bg-white/80 backdrop-blur-sm hover:bg-white shadow-sm"
                />
              )}
              <ShareButton productName={product.name} productId={product.id} />
            </div>
          </div>

          {/* ── Content Section ── */}
          <div className="bg-[hsl(var(--background))]">
            <div className="p-4 flex flex-col gap-4">

              {/* Header */}
              <div>
                <h2 className="text-lg font-serif font-semibold text-[hsl(var(--foreground))] leading-snug mb-0.5">
                  {product.name}
                </h2>
                {product.brand && (
                  <p className="text-sm text-[hsl(var(--foreground-secondary))]">{product.brand}</p>
                )}
              </div>

              {/* Price */}
              <div>
                <div className="flex items-baseline gap-2">
                  <span className="text-xl font-bold text-primary tracking-tight">
                    ${currentPrice.toFixed(2)}
                  </span>
                  {hasPromo && (
                    <span className="text-sm line-through text-[hsl(var(--foreground-tertiary))]">
                      ${product.price.price_nzd.toFixed(2)}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-x-3 text-xs text-[hsl(var(--foreground-secondary))] mt-0.5">
                  {product.price.price_per_100ml && (
                    <span>${product.price.price_per_100ml.toFixed(2)} / 100ml</span>
                  )}
                  {product.price.price_per_standard_drink && (
                    <span>${product.price.price_per_standard_drink.toFixed(2)} / std drink</span>
                  )}
                </div>
              </div>

              {/* Promo info badges */}
              {hasPromo && (product.price.is_member_only || promoEndText) && (
                <div className="flex flex-wrap gap-2">
                  {product.price.is_member_only && (
                    <Badge variant="outline" className="gap-1 text-gold border-gold font-medium">
                      <Crown className="h-3 w-3" />
                      Members Only
                    </Badge>
                  )}
                  {promoEndText && (
                    <Badge variant="outline" className="gap-1 text-primary border-primary/30 font-medium">
                      <Clock className="h-3 w-3" />
                      {promoEndText}
                    </Badge>
                  )}
                </div>
              )}

              {/* Store & distance */}
              <div className="flex items-center justify-between gap-3 py-3 border-y border-[hsl(var(--border))]">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Store className="h-4 w-4 text-primary" />
                  </div>
                  <span className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                    {product.price.store_name}
                  </span>
                </div>
                {distanceText && (
                  <span className={cn("flex items-center gap-1 text-sm font-medium flex-shrink-0", distanceColorClass)}>
                    <MapPin className="h-3.5 w-3.5" />
                    {distanceText}
                  </span>
                )}
              </div>

              {/* Product details chips */}
              {details.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {details.map((d) => (
                    <span
                      key={d.label}
                      className="inline-flex items-center gap-1.5 text-xs bg-white text-[hsl(var(--foreground-secondary))] rounded-full px-3 py-1.5 border border-[hsl(var(--border))]"
                    >
                      <span className="font-medium text-[hsl(var(--foreground))]">{d.label}</span>
                      <span className="capitalize">{d.value}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-1">
                {product.product_url && (
                  <Button asChild className="flex-1 bg-primary hover:bg-primary/90 h-11 text-sm font-semibold shadow-sm">
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
                <PriceAlertButton
                  productId={product.id}
                  productName={product.name}
                  currentPrice={currentPrice}
                />
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
