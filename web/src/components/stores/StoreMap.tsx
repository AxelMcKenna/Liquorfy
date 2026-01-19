import { useEffect, useState, useMemo, useCallback } from 'react';
import Map, { Marker, Source, Layer, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Navigation, MapPin } from 'lucide-react';
import { Store, Location } from '@/types';
import { getChainColor, getChainName } from '@/lib/chainConstants';
import { ChainLogo } from './logos';
import { formatDistance, getDistanceColorClass } from '@/lib/formatters';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// Memoized circle calculation - only recalculates when center or radius changes
const createCircle = (center: [number, number], radiusInKm: number) => {
  const points = 64;
  const coords = {
    latitude: center[1],
    longitude: center[0],
  };

  const km = radiusInKm;
  const ret = [];
  const distanceX = km / (111.32 * Math.cos((coords.latitude * Math.PI) / 180));
  const distanceY = km / 110.574;

  for (let i = 0; i < points; i++) {
    const theta = (i / points) * (2 * Math.PI);
    const x = distanceX * Math.cos(theta);
    const y = distanceY * Math.sin(theta);
    ret.push([coords.longitude + x, coords.latitude + y]);
  }
  ret.push(ret[0]);

  return {
    type: 'Feature' as const,
    geometry: {
      type: 'Polygon' as const,
      coordinates: [ret],
    },
    properties: {},
  };
};

export interface StoreMapProps {
  userLocation: Location;
  stores: Store[];
  selectedStore?: Store | null;
  onStoreClick?: (store: Store) => void;
  radiusKm: number;
  onLocationChange?: (lat: number, lon: number) => void;
  isDraggable?: boolean;
}

export const StoreMap: React.FC<StoreMapProps> = ({
  userLocation,
  stores,
  selectedStore = null,
  onStoreClick,
  radiusKm,
  onLocationChange,
  isDraggable = false,
}) => {
  const [popupInfo, setPopupInfo] = useState<Store | null>(null);
  const [draggableLocation, setDraggableLocation] = useState(userLocation);
  const [viewState, setViewState] = useState({
    longitude: userLocation.lon,
    latitude: userLocation.lat,
    zoom: 12,
  });

  useEffect(() => {
    setViewState({
      longitude: userLocation.lon,
      latitude: userLocation.lat,
      zoom: 12,
    });
    setDraggableLocation(userLocation);
  }, [userLocation]);

  const handleMarkerDragEnd = useCallback((event: any) => {
    const { lngLat } = event;
    const newLocation = {
      lat: lngLat.lat,
      lon: lngLat.lng,
    };
    setDraggableLocation(newLocation);
    if (onLocationChange) {
      onLocationChange(lngLat.lat, lngLat.lng);
    }
  }, [onLocationChange]);

  const activeLocation = isDraggable ? draggableLocation : userLocation;

  // Memoize the radius circle - only recalculates when location or radius changes
  const radiusCircle = useMemo(
    () => createCircle([activeLocation.lon, activeLocation.lat], radiusKm),
    [activeLocation.lon, activeLocation.lat, radiusKm]
  );

  // Memoize store markers to prevent unnecessary re-renders
  const storeMarkers = useMemo(() => {
    return stores.map((store) => {
      const color = getChainColor(store.chain);
      const isSelected = selectedStore?.id === store.id;
      return { store, color, isSelected };
    });
  }, [stores, selectedStore?.id]);

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden shadow-lg border border-border">
      <Map
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        style={{ width: '100%', height: '100%' }}
      >
        {/* Radius circle */}
        <Source id="radius" type="geojson" data={radiusCircle}>
          <Layer
            id="radius-fill"
            type="fill"
            paint={{
              'fill-color': '#3b82f6',
              'fill-opacity': 0.1,
            }}
          />
          <Layer
            id="radius-outline"
            type="line"
            paint={{
              'line-color': '#3b82f6',
              'line-width': 2,
              'line-opacity': 0.6,
            }}
          />
        </Source>

        {/* User location marker */}
        <Marker
          longitude={activeLocation.lon}
          latitude={activeLocation.lat}
          anchor="center"
          draggable={isDraggable}
          onDragEnd={handleMarkerDragEnd}
        >
          <div className="relative">
            {!isDraggable && (
              <div className="absolute -inset-2 bg-location rounded-full animate-ping opacity-75" />
            )}
            <div
              className={cn(
                "relative bg-location p-2 rounded-full shadow-lg border-2 border-white",
                isDraggable && "cursor-move"
              )}
            >
              <Navigation className="h-5 w-5 text-white" />
            </div>
          </div>
        </Marker>

        {/* Store markers - using memoized data */}
        {storeMarkers.map(({ store, color, isSelected }) => (
          <Marker
            key={store.id}
            longitude={store.lon}
            latitude={store.lat}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setPopupInfo(store);
            }}
          >
            <div
              className={`cursor-pointer transition-transform hover:scale-110 ${
                isSelected ? 'scale-125' : ''
              }`}
            >
              <div
                className="relative"
                style={{
                  filter: isSelected ? 'drop-shadow(0 0 8px rgba(34, 197, 94, 0.8))' : '',
                }}
              >
                <svg
                  width="46"
                  height="58"
                  viewBox="0 0 40 50"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M20 0C8.95 0 0 8.95 0 20C0 35 20 50 20 50C20 50 40 35 40 20C40 8.95 31.05 0 20 0Z"
                    fill={color}
                  />
                  <circle cx="20" cy="18" r="10" fill="white" />
                </svg>
                <div className="absolute top-[8px] left-1/2 transform -translate-x-1/2">
                  <ChainLogo chain={store.chain} className="h-5 w-5" color={color} />
                </div>
              </div>
            </div>
          </Marker>
        ))}

        {/* Popup */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.lon}
            latitude={popupInfo.lat}
            anchor="top"
            onClose={() => setPopupInfo(null)}
            closeButton={true}
            closeOnClick={false}
            maxWidth="280px"
          >
            <div className="p-3 pr-8">
              {/* Header: Logo + Store name */}
              <div className="flex items-start gap-2.5 mb-2">
                <div
                  className="p-1.5 rounded shrink-0"
                  style={{ backgroundColor: getChainColor(popupInfo.chain) }}
                >
                  <ChainLogo chain={popupInfo.chain} className="h-4 w-4 text-white" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-primary-gray text-sm leading-tight">
                    {popupInfo.name}
                  </h3>
                  <p className="text-xs text-secondary-gray mt-0.5 line-clamp-2">
                    {popupInfo.address}
                  </p>
                </div>
              </div>

              {/* Distance */}
              {formatDistance(popupInfo.distance_km) && (
                <div className={cn(
                  "flex items-center gap-1 text-xs font-medium mb-3",
                  getDistanceColorClass(popupInfo.distance_km)
                )}>
                  <MapPin className="h-3.5 w-3.5" />
                  <span>{formatDistance(popupInfo.distance_km)} away</span>
                </div>
              )}

              {/* Select button */}
              {onStoreClick && (
                <Button
                  onClick={() => {
                    onStoreClick(popupInfo);
                    setPopupInfo(null);
                  }}
                  className="w-full"
                  size="sm"
                >
                  Select Store
                </Button>
              )}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
};
