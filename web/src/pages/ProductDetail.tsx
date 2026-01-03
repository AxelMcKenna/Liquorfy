import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, ExternalLink, Store, Wine, MapPin, Clock, Crown } from 'lucide-react';
import { Product } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Header } from '@/components/layout/Header';

export const ProductDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/products/${id}`);

        if (!response.ok) {
          throw new Error('Product not found');
        }

        const data = await response.json();
        setProduct(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load product');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProduct();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-secondary">
        <Header query="" setQuery={() => {}} onSearch={() => {}} variant="compact" />
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
            <p className="text-lg text-secondary-gray">Loading product...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-secondary">
        <Header query="" setQuery={() => {}} onSearch={() => {}} variant="compact" />
        <div className="flex items-center justify-center min-h-[60vh]">
          <Card className="max-w-md mx-4">
            <CardContent className="p-8 text-center">
              <Wine className="h-16 w-16 text-tertiary-gray mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-2 text-primary-gray">Product Not Found</h2>
              <p className="text-secondary-gray mb-6">{error || 'This product could not be found.'}</p>
              <Button onClick={() => navigate(-1)}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Go Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const hasPromo = product.price.promo_price_nzd && product.price.promo_price_nzd < product.price.price_nzd;
  const currentPrice = product.price.promo_price_nzd ?? product.price.price_nzd;

  return (
    <div className="min-h-screen bg-secondary">
      <Header query="" setQuery={() => {}} onSearch={() => {}} variant="compact" />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Results
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:items-stretch">
          {/* Product Image */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="h-full"
          >
            <Card className="glass-card rounded-card-xl overflow-hidden h-full">
              <div className="aspect-square lg:aspect-auto lg:h-full bg-white p-8 flex items-center justify-center">
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-tertiary', 'to-secondary');
                    }}
                  />
                ) : (
                  <Wine className="h-32 w-32 text-tertiary-gray/30" />
                )}
              </div>
            </Card>
          </motion.div>

          {/* Product Info */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="h-full"
          >
            <Card className="glass-card rounded-card-xl h-full flex flex-col">
              <CardContent className="p-6 space-y-6">
                <div>
                  {hasPromo && (
                    <Badge className="mb-3 promo-badge">SALE</Badge>
                  )}
                  <h1 className="text-4xl font-bold text-primary-gray mb-2">{product.name}</h1>
                  {product.brand && (
                    <p className="text-xl text-secondary-gray">{product.brand}</p>
                  )}
                </div>

                <div>
                  <div className="flex items-baseline gap-3 mb-4">
                    <span className="text-5xl font-black text-primary">
                      ${currentPrice.toFixed(2)}
                    </span>
                    {hasPromo && (
                      <span className="text-xl line-through text-tertiary-gray">
                        ${product.price.price_nzd.toFixed(2)}
                      </span>
                    )}
                  </div>

                  {/* Price metrics */}
                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
                    {product.price.price_per_100ml && (
                      <>
                        <dt className="text-secondary-gray">Per 100ml</dt>
                        <dd className="font-medium text-primary-gray">
                          ${product.price.price_per_100ml.toFixed(2)}
                        </dd>
                      </>
                    )}
                    {product.price.price_per_standard_drink && (
                      <>
                        <dt className="text-secondary-gray">Per standard drink</dt>
                        <dd className="font-medium text-primary-gray">
                          ${product.price.price_per_standard_drink.toFixed(2)}
                        </dd>
                      </>
                    )}
                  </dl>

                  {/* Promo badges */}
                  {hasPromo && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {product.price.is_member_only && (
                        <Badge variant="secondary" className="gap-1 bg-gold/20 text-gold border-gold/30">
                          <Crown className="h-3 w-3" />
                          Members Only
                        </Badge>
                      )}
                      {product.price.promo_ends_at && (
                        <Badge variant="outline" className="gap-1 text-primary border-primary/30">
                          <Clock className="h-3 w-3" />
                          {new Date(product.price.promo_ends_at).toLocaleDateString('en-NZ')}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>

                {/* Store info */}
                <div className="pt-6 border-t border-subtle">
                  <div className="flex items-center gap-2 text-secondary-gray mb-4">
                    <Store className="h-5 w-5 text-primary" />
                    <div>
                      <p className="font-semibold text-primary-gray">{product.price.store_name}</p>
                      <p className="text-sm">{product.chain}</p>
                    </div>
                  </div>

                  {product.product_url && (
                    <Button asChild className="w-full bg-primary hover:bg-accent text-white" size="lg">
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
              </CardContent>
            </Card>
          </motion.div>

          {/* Product Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="lg:col-span-2"
          >
            <Card className="glass-card rounded-card-xl">
              <CardContent className="p-6">
                <h2 className="text-xl font-semibold mb-4 text-primary-gray">Product Details</h2>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                  {product.category && (
                    <>
                      <dt className="text-secondary-gray">Category</dt>
                      <dd className="font-medium text-primary-gray capitalize">{product.category.replace('_', ' ')}</dd>
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
                  {product.price.standard_drinks && (
                    <>
                      <dt className="text-secondary-gray">Standard Drinks</dt>
                      <dd className="font-medium text-primary-gray">{product.price.standard_drinks}</dd>
                    </>
                  )}
                </dl>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </main>
    </div>
  );
};

export default ProductDetail;
