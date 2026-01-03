import { useEffect, useRef, useState } from 'react';
import Map, { Marker, Source, Layer, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Navigation } from 'lucide-react';
import { Store, Location } from '@/types';
import { chainColors, chainNames, getChainColor, getChainName } from '@/lib/chainConstants';
import { ChainLogo } from './logos';

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

  const handleMarkerDragEnd = (event: any) => {
    const { lngLat } = event;
    const newLocation = {
      lat: lngLat.lat,
      lon: lngLat.lng,
    };
    setDraggableLocation(newLocation);
    if (onLocationChange) {
      onLocationChange(lngLat.lat, lngLat.lng);
    }
  };

  // Create GeoJSON for the radius circle
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

  const activeLocation = isDraggable ? draggableLocation : userLocation;
  const radiusCircle = createCircle([activeLocation.lon, activeLocation.lat], radiusKm);

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden shadow-lg border-2 border-gray-200">
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
              <div className="absolute -inset-2 bg-blue-500 rounded-full animate-ping opacity-75" />
            )}
            <div
              className={`relative bg-blue-600 p-2 rounded-full shadow-lg border-3 border-white ${
                isDraggable ? 'cursor-move' : ''
              }`}
            >
              <Navigation className="h-5 w-5 text-white" />
            </div>
          </div>
        </Marker>

        {/* Store markers */}
        {stores.map((store) => {
          const color = getChainColor(store.chain);
          const isSelected = selectedStore?.id === store.id;

          return (
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
                    width="40"
                    height="50"
                    viewBox="0 0 40 50"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M20 0C8.95 0 0 8.95 0 20C0 35 20 50 20 50C20 50 40 35 40 20C40 8.95 31.05 0 20 0Z"
                      fill={color}
                    />
                    <circle cx="20" cy="18" r="8" fill="white" />
                  </svg>
                  <div className="absolute top-[8px] left-1/2 transform -translate-x-1/2">
                    <ChainLogo chain={store.chain} className="h-4 w-4" color={color} />
                  </div>
                </div>
              </div>
            </Marker>
          );
        })}

        {/* Popup */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.lon}
            latitude={popupInfo.lat}
            anchor="top"
            onClose={() => setPopupInfo(null)}
            closeButton={true}
            closeOnClick={false}
            className="store-popup"
          >
            <div className="p-3 min-w-[220px]">
              <div className="mb-2">
                <div
                  className="inline-block px-2 py-1 rounded text-xs font-semibold text-white mb-2"
                  style={{ backgroundColor: getChainColor(popupInfo.chain) }}
                >
                  {getChainName(popupInfo.chain)}
                </div>
              </div>
              <h3 className="font-bold text-gray-900 mb-1">{popupInfo.name}</h3>
              <p className="text-sm text-gray-600 mb-2">{popupInfo.address}</p>
              {popupInfo.distance_km !== null && popupInfo.distance_km !== undefined && (
                <p className="text-sm font-semibold text-blue-600 mb-3">
                  📍 {popupInfo.distance_km.toFixed(1)} km away
                </p>
              )}
              {onStoreClick && (
                <button
                  onClick={() => {
                    onStoreClick(popupInfo);
                    setPopupInfo(null);
                  }}
                  className="w-full px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-sm font-semibold hover:from-blue-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg"
                >
                  Select This Store
                </button>
              )}
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
};
