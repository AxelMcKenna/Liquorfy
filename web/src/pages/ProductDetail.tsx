import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProductDetail } from '@/hooks/useProductDetail';
import { useFavourites } from '@/hooks/useFavourites';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { useLocationContext } from '@/contexts/LocationContext';
import { FavouriteButton } from '@/components/products/FavouriteButton';
import { ShareButton } from '@/components/products/ShareButton';
import api from '@/lib/api';
import { PriceAlertButton } from '@/components/alerts/PriceAlertButton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { PriceHistoryChart } from '@/components/products/PriceHistoryChart';
import { cn } from '@/lib/utils';
import {
  formatPromoEndDate,
  calculateSavingsPercent,
} from '@/lib/formatters';
import {
  ArrowLeft,
  ExternalLink,
  Store as StoreIcon,
  Clock,
  Crown,
  Wine,
  Sparkles,
  Search,
  ArrowRight,
  ChevronRight,
  Home,
} from 'lucide-react';
import { Price, CrossChainPrice } from '@/types';
import { Link } from 'react-router-dom';
import { RecentlyViewed } from '@/components/products/RecentlyViewed';
import { Skeleton } from '@/components/ui/skeleton';

const PriceRow = ({ price, isBest }: { price: Price; isBest?: boolean }) => {
  const effective = price.promo_price_nzd ?? price.price_nzd;
  const hasPromo = price.promo_price_nzd != null && price.promo_price_nzd < price.price_nzd;

  return (
    <div className={cn(
      "flex items-center justify-between gap-4 p-3 rounded-lg border",
      isBest ? "border-primary/30 bg-primary/5" : "border-[hsl(var(--border))] bg-white"
    )}>
      <div className="flex items-center gap-3 min-w-0">
        <div className={cn(
          "h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0",
          isBest ? "bg-primary/15" : "bg-secondary"
        )}>
          <StoreIcon className={cn("h-4 w-4", isBest ? "text-primary" : "text-muted-foreground")} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
            {price.store_name}
          </p>
          <p className="text-xs text-[hsl(var(--foreground-secondary))] capitalize">
            {price.chain.replace('_', ' ')}
            {price.distance_km != null && ` · ${price.distance_km} km`}
          </p>
        </div>
      </div>
      <div className="text-right flex-shrink-0">
        <div className="flex items-baseline gap-1.5">
          {isBest && (
            <Badge className="bg-primary text-white text-[10px] px-1.5 py-0">Best</Badge>
          )}
          <span className={cn("font-bold", isBest ? "text-primary text-base" : "text-[hsl(var(--foreground))] text-sm")}>
            ${effective.toFixed(2)}
          </span>
        </div>
        {hasPromo && (
          <span className="text-xs line-through text-[hsl(var(--foreground-tertiary))]">
            ${price.price_nzd.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
};

const CrossChainRow = ({ item }: { item: CrossChainPrice }) => {
  const navigate = useNavigate();
  const effective = item.promo_price_nzd ?? item.price_nzd;
  const hasPromo = item.promo_price_nzd != null && item.promo_price_nzd < item.price_nzd;

  return (
    <button
      onClick={() => navigate(`/product/${item.product_id}`)}
      className="flex items-center justify-between gap-4 p-3 rounded-lg border border-[hsl(var(--border))] bg-white hover:border-primary/30 hover:bg-primary/5 transition-colors text-left w-full"
    >
      <div className="flex items-center gap-3 min-w-0">
        <div className="h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 bg-secondary">
          <StoreIcon className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
            {item.store_name}
          </p>
          <p className="text-xs text-[hsl(var(--foreground-secondary))] capitalize">
            {item.chain.replace('_', ' ')}
            {item.distance_km != null && ` · ${item.distance_km} km`}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <div className="text-right">
          <span className="font-bold text-sm text-[hsl(var(--foreground))]">
            ${effective.toFixed(2)}
          </span>
          {hasPromo && (
            <span className="text-xs line-through text-[hsl(var(--foreground-tertiary))] ml-1">
              ${item.price_nzd.toFixed(2)}
            </span>
          )}
        </div>
        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
    </button>
  );
};

export const ProductDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { product, loading, error, fetchProduct } = useProductDetail();
  const { isFavourite, toggleFavourite } = useFavourites();
  const { addProduct, recentlyViewed } = useRecentlyViewed();
  const { location, radiusKm } = useLocationContext();

  useEffect(() => {
    if (id) {
      fetchProduct(id, location ? { lat: location.lat, lon: location.lon, radius_km: radiusKm } : undefined);
    }
  }, [id, fetchProduct, location, radiusKm]);

  useEffect(() => {
    if (product) addProduct(product);
  }, [product]); // eslint-disable-line react-hooks/exhaustive-deps

  // Fire-and-forget view tracking
  useEffect(() => {
    if (id) api.post(`/products/${id}/view`).catch(() => {});
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <PageHeader sticky />
        <main className="max-w-4xl mx-auto px-4 py-6 md:py-10 flex-1 w-full">
          {/* Breadcrumb skeleton */}
          <div className="flex items-center gap-2 mb-6">
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
            {/* Image skeleton */}
            <Skeleton className="aspect-square rounded-xl" />
            {/* Details skeleton */}
            <div className="flex flex-col gap-5">
              <div className="space-y-2">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-1/3" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-10 w-32" />
                <Skeleton className="h-4 w-48" />
              </div>
              <div className="flex gap-2">
                <Skeleton className="h-6 w-20 rounded-full" />
                <Skeleton className="h-6 w-24 rounded-full" />
              </div>
              <div className="flex gap-2 pt-1">
                <Skeleton className="h-11 flex-1" />
                <Skeleton className="h-11 w-11" />
              </div>
            </div>
          </div>
          {/* Price rows skeleton */}
          <div className="mt-10 space-y-3">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
          </div>
        </main>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-sm px-4">
          <Search className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
          <p className="text-lg font-medium text-foreground mb-1">Product not found</p>
          <p className="text-sm text-muted-foreground mb-6">This product may have been removed or the link is incorrect.</p>
          <Button onClick={() => navigate('/explore')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Browse products
          </Button>
        </div>
      </div>
    );
  }

  const hasPromo = product.price.promo_price_nzd != null && product.price.promo_price_nzd < product.price.price_nzd;
  const currentPrice = product.price.promo_price_nzd ?? product.price.price_nzd;
  const savingsPercent = calculateSavingsPercent(product.price.price_nzd, product.price.promo_price_nzd);
  const promoEndText = formatPromoEndDate(product.price.promo_ends_at);
  const isNewPromo = hasPromo && product.last_updated &&
    (Date.now() - new Date(product.last_updated).getTime()) < 24 * 60 * 60 * 1000;
  const favourite = isFavourite(product.id);

  const details = [
    product.category && { label: "Category", value: product.category.replace('_', ' ') },
    product.abv_percent && { label: "ABV", value: `${product.abv_percent}%` },
    product.total_volume_ml && { label: "Volume", value: `${product.total_volume_ml}ml` },
    product.pack_count && product.pack_count > 1 && { label: "Pack", value: `${product.pack_count} units` },
  ].filter(Boolean) as { label: string; value: string }[];

  const allPrices = [product.price, ...product.other_prices].slice(0, 5);
  const hasMultipleStores = allPrices.length > 1;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader
        sticky
        rightContent={
          <>
            <ShareButton productName={product.name} productId={product.id} className="text-white/70 hover:text-white hover:bg-white/10" />
            <FavouriteButton isFavourite={favourite} onToggle={() => toggleFavourite(product.id)} className="text-white/70 hover:text-white hover:bg-white/10" />
          </>
        }
      />

      <main className="max-w-4xl mx-auto px-4 py-6 md:py-10 flex-1">
        {/* Breadcrumbs */}
        <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground mb-6 overflow-x-auto no-scrollbar">
          <Link to="/" className="flex items-center gap-1 hover:text-foreground transition-colors flex-shrink-0">
            <Home className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Home</span>
          </Link>
          {product.category && (
            <>
              <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
              <Link
                to={`/explore?category=${product.category}`}
                className="hover:text-foreground transition-colors capitalize flex-shrink-0"
              >
                {product.category.replace(/_/g, ' ')}
              </Link>
            </>
          )}
          <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
          <span className="text-foreground font-medium truncate">{product.name}</span>
        </nav>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">

          {/* Left: Image */}
          <div className="relative flex items-center justify-center bg-white rounded-xl border border-[hsl(var(--border))] p-8 min-h-[320px] md:min-h-[420px]">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-72 md:h-96 object-contain drop-shadow-sm"
              />
            ) : (
              <Wine className="h-24 w-24 text-[hsl(var(--foreground-tertiary))]/30" />
            )}

            {/* Badges */}
            {hasPromo && (
              <div className="absolute top-4 left-4 flex flex-col gap-1.5">
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
          </div>

          {/* Right: Details */}
          <div className="flex flex-col gap-5">
            {/* Name & brand */}
            <div>
              <h1 className="text-2xl md:text-3xl font-serif font-semibold text-[hsl(var(--foreground))] leading-snug mb-1">
                {product.name}
              </h1>
              {product.brand && (
                <p className="text-sm text-[hsl(var(--foreground-secondary))]">{product.brand}</p>
              )}
            </div>

            {/* Price block */}
            <div>
              <div className="flex items-baseline gap-2.5">
                <span className="text-3xl font-bold text-primary tracking-tight">
                  ${currentPrice.toFixed(2)}
                </span>
                {hasPromo && (
                  <span className="text-base line-through text-[hsl(var(--foreground-tertiary))]">
                    ${product.price.price_nzd.toFixed(2)}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap gap-x-4 text-sm text-[hsl(var(--foreground-secondary))] mt-1">
                {product.price.price_per_100ml && (
                  <span>${product.price.price_per_100ml.toFixed(2)} / 100ml</span>
                )}
                {product.price.price_per_standard_drink && (
                  <span>${product.price.price_per_standard_drink.toFixed(2)} / std drink</span>
                )}
              </div>
            </div>

            {/* Promo badges */}
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

        {/* Compare prices section */}
        {hasMultipleStores && (
          <section className="mt-10 md:mt-14">
            <h2 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-4">
              Compare prices
              <span className="text-sm font-normal text-[hsl(var(--foreground-secondary))] ml-2">
                {allPrices.length} stores
              </span>
            </h2>
            <div className="flex flex-col gap-2">
              {allPrices.map((price, idx) => (
                <PriceRow key={price.store_id} price={price} isBest={idx === 0} />
              ))}
            </div>
          </section>
        )}

        {/* Price history chart */}
        {product.price_history && product.price_history.length > 1 && (
          <section className="mt-10 md:mt-14">
            <h2 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-4">
              Price history
              <span className="text-sm font-normal text-[hsl(var(--foreground-secondary))] ml-2">
                Last 30 days
              </span>
            </h2>
            <PriceHistoryChart history={product.price_history} />
          </section>
        )}

        {/* Cross-chain comparison */}
        {product.cross_chain_prices.length > 0 && (
          <section className="mt-10 md:mt-14">
            <h2 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-1">
              Compare across chains
            </h2>
            <p className="text-sm text-[hsl(var(--foreground-secondary))] mb-4">
              Same product at other retailers
            </p>
            <div className="flex flex-col gap-2">
              {product.cross_chain_prices.slice(0, 5).map((item) => (
                <CrossChainRow key={item.product_id} item={item} />
              ))}
            </div>
          </section>
        )}

        {/* Recently Viewed (excluding current product) */}
        <RecentlyViewed products={recentlyViewed.filter(p => p.id !== product.id)} />
      </main>

      <Footer />
    </div>
  );
};

export default ProductDetailPage;
