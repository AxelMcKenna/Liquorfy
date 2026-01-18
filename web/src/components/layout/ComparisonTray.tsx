import { useState } from "react";
import { X, Award, ShoppingCart, ExternalLink, ArrowUpDown, Share2, Check, ChevronDown, ChevronUp } from "lucide-react";
import { Product } from "@/types";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ComparisonTrayProps {
  products: Product[];
  onClear: () => void;
  onRemoveProduct?: (product: Product) => void;
  maxCompare?: number;
}

type SortBy = 'total_price' | 'price_per_100ml' | 'price_per_drink';

export const ComparisonTray = ({ products, onClear, onRemoveProduct, maxCompare = 4 }: ComparisonTrayProps) => {
  const [sortBy, setSortBy] = useState<SortBy>('price_per_100ml');
  const [shareSuccess, setShareSuccess] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (products.length === 0) return null;

  const handleShare = async () => {
    const productIds = products.map(p => p.id).join(',');
    const shareUrl = `${window.location.origin}/compare?products=${productIds}`;
    const shareText = `Check out my Liquorfy comparison of ${products.length} products!`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Liquorfy Product Comparison',
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }
      }
    }

    try {
      await navigator.clipboard.writeText(shareUrl);
      setShareSuccess(true);
      setTimeout(() => setShareSuccess(false), 2000);
      toast.success("Comparison link copied!", {
        description: "Share it with friends to compare products",
        duration: 3000,
      });
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      toast.error("Failed to copy link", {
        description: "Please try again",
        duration: 3000,
      });
    }
  };

  const sortedProducts = [...products].sort((a, b) => {
    const aPrice = a.price.promo_price_nzd ?? a.price.price_nzd;
    const bPrice = b.price.promo_price_nzd ?? b.price.price_nzd;

    switch (sortBy) {
      case 'total_price':
        return aPrice - bPrice;
      case 'price_per_100ml':
        return (a.price.price_per_100ml ?? Infinity) - (b.price.price_per_100ml ?? Infinity);
      case 'price_per_drink':
        return (a.price.price_per_standard_drink ?? Infinity) - (b.price.price_per_standard_drink ?? Infinity);
      default:
        return 0;
    }
  });

  const bestValue = sortedProducts[0];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-background border-t shadow-lg">
      <div className="max-w-6xl mx-auto px-4 py-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <ShoppingCart className="h-5 w-5 text-primary" />
            <span className="text-sm font-medium">
              Comparing <span className="text-primary">{products.length}</span>/{maxCompare}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="md:hidden h-8 w-8 p-0"
            >
              {isCollapsed ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
              <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortBy)}>
                <SelectTrigger className="w-[140px] h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="total_price">Cheapest</SelectItem>
                  <SelectItem value="price_per_100ml">Per 100ml</SelectItem>
                  <SelectItem value="price_per_drink">Per drink</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleShare}
              className="h-8"
            >
              {shareSuccess ? (
                <Check className="h-4 w-4" />
              ) : (
                <Share2 className="h-4 w-4" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                onClear();
                toast.info("Comparison cleared");
              }}
              className="h-8 w-8 p-0 hover:bg-destructive/10 hover:text-destructive"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {!isCollapsed && (
          <>
            <Separator className="mb-3" />

            {/* Products */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {sortedProducts.map((product) => (
                <div
                  key={product.id}
                  className="relative bg-secondary rounded-lg p-3 border flex flex-col"
                >
                  {/* Remove button */}
                  {onRemoveProduct && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="absolute top-1 right-1 h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveProduct(product);
                        toast.info("Removed from comparison");
                      }}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}

                  {/* Best value badge */}
                  {product.id === bestValue.id && (
                    <Badge className="absolute -top-2 left-2 bg-primary text-white text-xs gap-1">
                      <Award className="h-3 w-3" />
                      Best value
                    </Badge>
                  )}

                  {/* Thumbnail */}
                  {product.image_url && (
                    <div className="w-full h-16 mb-2 rounded overflow-hidden bg-background">
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-full object-contain p-1"
                      />
                    </div>
                  )}

                  <h4 className="text-sm font-medium line-clamp-2 mb-1">
                    {product.name}
                  </h4>
                  <p className="text-xs text-muted-foreground mb-2">
                    {product.price.store_name}
                  </p>
                  <p className="text-lg font-semibold text-primary">
                    ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
                  </p>
                  {product.price.price_per_100ml && (
                    <p className="text-xs text-muted-foreground mt-0.5 mb-2">
                      ${product.price.price_per_100ml.toFixed(2)} / 100ml
                    </p>
                  )}

                  {/* Purchase CTA */}
                  {product.product_url ? (
                    <Button
                      asChild
                      size="sm"
                      className="w-full mt-auto"
                    >
                      <a
                        href={product.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-1"
                      >
                        View at Store
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </Button>
                  ) : (
                    <p className="text-xs text-muted-foreground mt-auto text-center">
                      No link available
                    </p>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
