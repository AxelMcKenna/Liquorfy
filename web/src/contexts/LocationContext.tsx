import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Location } from '@/types';

interface LocationData {
  location: Location;
  source: 'auto' | 'manual';
  timestamp: number;
  radiusKm: number;
}

interface LocationContextType {
  location: Location | null;
  locationSource: 'auto' | 'manual' | null;
  isLocationSet: boolean;
  radiusKm: number;
  loading: boolean;
  error: string | null;
  setRadiusKm: (radius: number) => void;
  requestAutoLocation: () => Promise<void>;
  setManualLocation: (lat: number, lon: number) => void;
  clearLocation: () => void;
  openLocationModal: () => void;
  closeLocationModal: () => void;
  isLocationModalOpen: boolean;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

const STORAGE_KEY = 'userLocationData';
const DEFAULT_RADIUS_KM = 20;
const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes

export const LocationProvider = ({ children }: { children: ReactNode }) => {
  const [locationData, setLocationData] = useState<LocationData | null>(() => {
    // Initialize from localStorage
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const data: LocationData = JSON.parse(stored);
        // Check if cache is still valid
        if (Date.now() - data.timestamp < CACHE_DURATION_MS) {
          console.log('[LocationContext] Loaded cached location:', data);
          return data;
        }
      } catch (e) {
        console.error('[LocationContext] Failed to parse stored location data:', e);
      }
    }
    console.log('[LocationContext] No cached location found');
    return null;
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);

  // Persist to localStorage whenever locationData changes
  useEffect(() => {
    if (locationData) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(locationData));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [locationData]);

  const requestAutoLocation = async (): Promise<void> => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      throw new Error('Geolocation not supported');
    }

    setLoading(true);
    setError(null);

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const newLocation: Location = {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          };

          // Validate location is within New Zealand bounds
          const isInNZ =
            newLocation.lat >= -47 &&
            newLocation.lat <= -34 &&
            newLocation.lon >= 165 &&
            newLocation.lon <= 179;

          if (!isInNZ) {
            const errorMsg = 'Liquorfy is currently only available in New Zealand';
            setError(errorMsg);
            setLoading(false);
            reject(new Error(errorMsg));
            return;
          }

          setLocationData({
            location: newLocation,
            source: 'auto',
            timestamp: Date.now(),
            radiusKm: locationData?.radiusKm ?? DEFAULT_RADIUS_KM,
          });
          setLoading(false);
          resolve();
        },
        (err) => {
          let errorMessage = 'Failed to get your location';

          switch (err.code) {
            case err.PERMISSION_DENIED:
              errorMessage = 'Location permission denied. Please set your location manually.';
              break;
            case err.POSITION_UNAVAILABLE:
              errorMessage = 'Location information is unavailable.';
              break;
            case err.TIMEOUT:
              errorMessage = 'Location request timed out. Please try again.';
              break;
          }

          setError(errorMessage);
          setLoading(false);
          reject(new Error(errorMessage));
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000, // 5 minutes
        }
      );
    });
  };

  const setManualLocation = (lat: number, lon: number, radius?: number) => {
    // Validate location is within New Zealand bounds
    const isInNZ = lat >= -47 && lat <= -34 && lon >= 165 && lon <= 179;

    if (!isInNZ) {
      setError('Please select a location within New Zealand');
      return;
    }

    setLocationData({
      location: { lat, lon },
      source: 'manual',
      timestamp: Date.now(),
      radiusKm: radius ?? locationData?.radiusKm ?? DEFAULT_RADIUS_KM,
    });
    setError(null);
  };

  const setRadiusKm = (radius: number) => {
    // Enforce 5-40km range (matching backend validation)
    const clampedRadius = Math.max(5, Math.min(40, radius));

    if (locationData) {
      setLocationData({
        ...locationData,
        radiusKm: clampedRadius,
        timestamp: Date.now(), // Update timestamp when radius changes
      });
    }
  };

  const clearLocation = () => {
    setLocationData(null);
    setError(null);
  };

  const openLocationModal = () => {
    setIsLocationModalOpen(true);
  };

  const closeLocationModal = () => {
    setIsLocationModalOpen(false);
  };

  const value: LocationContextType = {
    location: locationData?.location ?? null,
    locationSource: locationData?.source ?? null,
    isLocationSet: locationData !== null,
    radiusKm: locationData?.radiusKm ?? DEFAULT_RADIUS_KM,
    loading,
    error,
    setRadiusKm,
    requestAutoLocation,
    setManualLocation,
    clearLocation,
    openLocationModal,
    closeLocationModal,
    isLocationModalOpen,
  };

  return (
    <LocationContext.Provider value={value}>
      {children}
    </LocationContext.Provider>
  );
};

export const useLocationContext = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocationContext must be used within LocationProvider');
  }
  return context;
};
