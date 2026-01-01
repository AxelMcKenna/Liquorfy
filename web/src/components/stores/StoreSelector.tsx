import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Navigation, Store as StoreIcon, X, Map } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { StoreMap } from '@/components/stores/StoreMap';
import { useLocation } from '@/hooks/useLocation';
import { useStores } from '@/hooks/useStores';
import { Store } from '@/types';

interface StoreSelectorProps {
  selectedStore: Store | null;
  onSelectStore: (store: Store | null) => void;
  onClose?: () => void;
}

const chainColors: Record<string, string> = {
  super_liquor: 'bg-red-500',
  liquorland: 'bg-blue-500',
  countdown: 'bg-green-500',
  new_world: 'bg-purple-500',
  pak_n_save: 'bg-yellow-500',
  bottle_o: 'bg-orange-500',
  liquor_centre: 'bg-indigo-500',
  glengarry: 'bg-pink-500',
};

const chainNames: Record<string, string> = {
  super_liquor: 'Super Liquor',
  liquorland: 'Liquorland',
  countdown: 'Countdown',
  new_world: 'New World',
  pak_n_save: "PAK'nSAVE",
  bottle_o: 'Bottle-O',
  liquor_centre: 'Liquor Centre',
  glengarry: 'Glengarry',
};

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

  const handleRequestLocation = () => {
    requestLocation();
  };

  const handleStoreClick = (store: Store) => {
    onSelectStore(store);
    onClose?.();
  };

  const handleClearSelection = () => {
    onSelectStore(null);
  };

  return (
    <div className="space-y-4">
      {/* Location Request */}
      {!location && (
        <Card className="p-6">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Navigation className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2">Find Stores Near You</h3>
              <p className="text-gray-600 text-sm mb-4">
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
              <p className="text-red-600 text-sm">{locationError}</p>
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
          <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <div className={`p-2 ${chainColors[selectedStore.chain] || 'bg-gray-500'} rounded-lg`}>
                  <StoreIcon className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{selectedStore.name}</h4>
                  <p className="text-sm text-gray-600">{selectedStore.address}</p>
                  {selectedStore.distance_km !== null && selectedStore.distance_km !== undefined && (
                    <div className="flex items-center mt-1 text-sm text-gray-500">
                      <MapPin className="h-3 w-3 mr-1" />
                      {selectedStore.distance_km.toFixed(1)} km away
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearSelection}
                className="text-gray-500 hover:text-gray-700"
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
            <h3 className="font-semibold text-gray-900">
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
          <Card className="p-4 bg-blue-50 border-blue-200">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Search Radius
                </label>
                <span className="text-sm font-semibold text-blue-600">
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
              <div className="flex justify-between text-xs text-gray-500">
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
              <StoreMap
                userLocation={location}
                stores={stores}
                selectedStore={selectedStore}
                onStoreClick={handleStoreClick}
                radiusKm={radiusKm}
              />
            </motion.div>
          )}

          {storesLoading && (
            <div className="text-center py-8 text-gray-500">
              Loading nearby stores...
            </div>
          )}

          {storesError && (
            <div className="text-center py-4 text-red-600">
              {storesError}
            </div>
          )}

          {!storesLoading && stores.length === 0 && (
            <Card className="p-6 text-center">
              <p className="text-gray-600">No stores found within 20km of your location</p>
            </Card>
          )}

          <AnimatePresence>
            {stores.map((store, index) => (
              <motion.div
                key={store.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className="p-4 hover:shadow-md transition-shadow cursor-pointer border-2 hover:border-blue-300"
                  onClick={() => handleStoreClick(store)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className={`p-2 ${chainColors[store.chain] || 'bg-gray-500'} rounded-lg`}>
                        <StoreIcon className="h-4 w-4 text-white" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gray-900">{store.name}</h4>
                          <Badge variant="secondary" className="text-xs">
                            {chainNames[store.chain] || store.chain}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">{store.address}</p>
                        {store.distance_km !== null && store.distance_km !== undefined && (
                          <div className="flex items-center mt-2 text-sm text-gray-500">
                            <MapPin className="h-3 w-3 mr-1" />
                            {store.distance_km.toFixed(1)} km away
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
