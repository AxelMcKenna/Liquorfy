import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Navigation, X, Map } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { LazyStoreMap } from '@/components/stores/LazyStoreMap';
import { useLocation } from '@/hooks/useLocation';
import { useStores } from '@/hooks/useStores';
import { Store } from '@/types';
import { getChainColorClass, getChainName } from '@/lib/chainConstants';
import { ChainLogo } from '@/components/stores/logos';
import { formatDistance, getDistanceColorClass } from '@/lib/formatters';
import { cn } from '@/lib/utils';

interface StoreSelectorProps {
  selectedStore: Store | null;
  onSelectStore: (store: Store | null) => void;
  onClose?: () => void;
}

export const StoreSelector: React.FC<StoreSelectorProps> = ({
  selectedStore,
  onSelectStore,
  onClose,
}) => {
  const { location, loading: locationLoading, error: locationError, requestLocation } = useLocation();
  const { stores, loading: storesLoading, error: storesError, fetchNearbyStores } = useStores();
  const [radiusKm, setRadiusKm] = useState(20);
  const [showMap, setShowMap] = useState(false);

  useEffect(() => {
    if (location && !storesLoading) {
      fetchNearbyStores(location, radiusKm);
    }
  }, [location, radiusKm, fetchNearbyStores]);

  const handleRequestLocation = useCallback(() => {
    requestLocation();
  }, [requestLocation]);

  const handleStoreClick = useCallback((store: Store) => {
    onSelectStore(store);
    onClose?.();
  }, [onSelectStore, onClose]);

  const handleClearSelection = useCallback(() => {
    onSelectStore(null);
  }, [onSelectStore]);

  return (
    <div className="space-y-4">
      {/* Location Request */}
      {!location && (
        <Card className="p-6">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="p-3 bg-location/10 rounded-full">
              <Navigation className="h-6 w-6 text-location" />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-primary-gray mb-2">Find Stores Near You</h3>
              <p className="text-secondary-gray text-sm mb-4">
                Enable location to see stores in your area and get accurate pricing
              </p>
              <Button
                onClick={handleRequestLocation}
                disabled={locationLoading}
                className="w-full sm:w-auto"
              >
                {locationLoading ? 'Getting Location...' : 'Enable Location'}
              </Button>
            </div>
            {locationError && (
              <p className="text-destructive text-sm">{locationError}</p>
            )}
          </div>
        </Card>
      )}

      {/* Selected Store Display */}
      {selectedStore && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
        >
          <Card className="p-4 bg-primary/5 border-primary/20">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className={`p-2 ${getChainColorClass(selectedStore.chain)} rounded-lg`}>
                  <ChainLogo chain={selectedStore.chain} className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h4 className="font-semibold text-primary-gray">{selectedStore.name}</h4>
                  <p className="text-sm text-secondary-gray">{selectedStore.address}</p>
                  {formatDistance(selectedStore.distance_km) && (
                    <div className={cn(
                      "flex items-center mt-1 text-sm",
                      getDistanceColorClass(selectedStore.distance_km)
                    )}>
                      <MapPin className="h-3 w-3 mr-1" />
                      {formatDistance(selectedStore.distance_km)} away
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearSelection}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Stores List */}
      {location && !selectedStore && (
        <div className="space-y-3">
          {/* Header with Map Toggle */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-primary-gray">
              Stores Near You ({stores.length})
            </h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowMap(!showMap)}
              className="flex items-center gap-2"
            >
              <Map className="h-4 w-4" />
              {showMap ? 'Hide Map' : 'Show Map'}
            </Button>
          </div>

          {/* Radius Slider */}
          <Card className="p-4 bg-secondary border-border">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-secondary-gray">
                  Search Radius
                </label>
                <span className="text-sm font-semibold text-primary">
                  {radiusKm} km
                </span>
              </div>
              <Slider
                value={[radiusKm]}
                onValueChange={(value) => setRadiusKm(value[0])}
                min={0}
                max={40}
                step={5}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-tertiary-gray">
                <span>0 km</span>
                <span>40 km</span>
              </div>
            </div>
          </Card>

          {/* Map View */}
          {showMap && location && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <LazyStoreMap
                userLocation={location}
                stores={stores}
                selectedStore={selectedStore}
                onStoreClick={handleStoreClick}
                radiusKm={radiusKm}
                fallbackClassName="h-[500px]"
              />
            </motion.div>
          )}

          {storesLoading && (
            <div className="text-center py-8 text-secondary-gray">
              Loading nearby stores...
            </div>
          )}

          {storesError && (
            <div className="text-center py-4 text-destructive">
              {storesError}
            </div>
          )}

          {!storesLoading && stores.length === 0 && (
            <Card className="p-6 text-center">
              <p className="text-secondary-gray">No stores found within {radiusKm}km of your location</p>
            </Card>
          )}

          <AnimatePresence>
            {stores.map((store, index) => (
              <motion.div
                key={store.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                // Limit staggered animation to first 10 items to prevent performance issues
                transition={{ delay: Math.min(index, 10) * 0.03 }}
              >
                <Card
                  className="p-4 hover:shadow-md transition-shadow cursor-pointer border hover:border-primary/30"
                  onClick={() => handleStoreClick(store)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className={`p-2 ${getChainColorClass(store.chain)} rounded-lg`}>
                        <ChainLogo chain={store.chain} className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-primary-gray">{store.name}</h4>
                          <Badge variant="secondary" className="text-xs">
                            {getChainName(store.chain)}
                          </Badge>
                        </div>
                        <p className="text-sm text-secondary-gray">{store.address}</p>
                        {formatDistance(store.distance_km) && (
                          <div className={cn(
                            "flex items-center mt-2 text-sm",
                            getDistanceColorClass(store.distance_km)
                          )}>
                            <MapPin className="h-3 w-3 mr-1" />
                            {formatDistance(store.distance_km)} away
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};
