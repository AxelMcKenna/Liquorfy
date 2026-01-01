import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Award, ShoppingCart, ExternalLink, ArrowUpDown, Share2, Check, ChevronDown, ChevronUp } from "lucide-react";
import { Product } from "@/types";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
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

    // Try Web Share API first
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Liquorfy Product Comparison',
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (err) {
        // User cancelled or error occurred, fall through to clipboard
        if ((err as Error).name === 'AbortError') {
          return; // User cancelled, don't show copied message
        }
      }
    }

    // Fallback to clipboard
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

  // Sort products based on selected criteria
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

  // Best value is the first item after sorting
  const bestValue = sortedProducts[0];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="fixed bottom-0 left-0 right-0 z-50"
      >
        <div className="bg-white border-t border-subtle shadow-2xl">
          <div className="max-w-7xl mx-auto px-4 py-6">
            {/* Header with count and sort */}
            <div className="flex items-center justify-between mb-4 gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-card">
                  <ShoppingCart className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-xl font-bold text-primary-gray">
                  Comparing <span className="text-primary">{products.length}</span>/{maxCompare} Products
                </h3>
                {/* Mobile collapse button */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsCollapsed(!isCollapsed)}
                  className="md:hidden"
                >
                  {isCollapsed ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                </Button>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <ArrowUpDown className="h-4 w-4 text-secondary-gray" />
                  <span className="text-sm text-secondary-gray hidden md:inline">Sort by:</span>
                  <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortBy)}>
                    <SelectTrigger className="w-[140px] md:w-[180px] h-9">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="total_price">Cheapest Price</SelectItem>
                      <SelectItem value="price_per_100ml">Best per 100ml</SelectItem>
                      <SelectItem value="price_per_drink">Best per Drink</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleShare}
                  className="hover:bg-primary/10 border-primary/20"
                >
                  {shareSuccess ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      <span className="hidden sm:inline">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Share2 className="h-4 w-4 sm:mr-2" />
                      <span className="hidden sm:inline">Share</span>
                    </>
                  )}
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    onClear();
                    toast.info("Comparison cleared", {
                      description: "All products removed from comparison",
                      duration: 2000,
                    });
                  }}
                  className="hover:bg-red-50 hover:text-red-600"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            {!isCollapsed && (
              <>
                <Separator className="mb-4 bg-border" />

                {/* Product comparison cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {sortedProducts.map((product, index) => (
                <motion.div
                  key={product.id}
                  initial={{ scale: 0.8, opacity: 0, y: 20 }}
                  animate={{ scale: 1, opacity: 1, y: 0 }}
                  exit={{ scale: 0.8, opacity: 0, y: 20 }}
                  transition={{ delay: index * 0.05, type: "spring" }}
                  className="relative bg-tertiary rounded-card-xl p-4 border border-subtle hover:shadow-md transition-shadow flex flex-col"
                >
                  {/* Best value badge */}
                  {/* Remove button */}
                  {onRemoveProduct && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute top-1 right-1 h-6 w-6 rounded-full bg-white/90 hover:bg-red-50 hover:text-red-600 z-20"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveProduct(product);
                        toast.info("Removed from comparison", {
                          description: product.name,
                          duration: 2000,
                        });
                      }}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}

                  {/* Best value badge */}
                  {product.id === bestValue.id && (
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", delay: 0.2 }}
                      className="absolute -top-3 -right-3 bg-gold text-white rounded-full p-2 shadow-lg z-10"
                    >
                      <Award className="h-5 w-5" />
                    </motion.div>
                  )}

                  {/* Product thumbnail */}
                  {product.image_url && (
                    <div className="w-full h-20 mb-3 rounded-card overflow-hidden bg-white">
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-full object-contain p-2"
                      />
                    </div>
                  )}

                  <h4 className="font-semibold text-sm line-clamp-2 mb-2 text-primary-gray">
                    {product.name}
                  </h4>
                  <p className="text-xs text-tertiary-gray mb-2">{product.price.store_name}</p>
                  <p className="text-2xl font-black text-primary">
                    ${(product.price.promo_price_nzd ?? product.price.price_nzd).toFixed(2)}
                  </p>
                  {product.price.price_per_100ml && (
                    <p className="text-xs text-secondary-gray mt-1 mb-3">
                      ${product.price.price_per_100ml.toFixed(2)} / 100ml
                    </p>
                  )}

                  {/* Purchase CTA */}
                  {product.product_url ? (
                    <Button
                      asChild
                      size="sm"
                      className="w-full mt-auto bg-primary hover:bg-accent text-white"
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
                    <p className="text-xs text-tertiary-gray mt-2 text-center">No link available</p>
                  )}
                </motion.div>
              ))}
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
