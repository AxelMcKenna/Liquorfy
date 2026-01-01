import { useState, useEffect } from 'react';
import { Location } from '@/types';

interface UseLocationReturn {
  location: Location | null;
  loading: boolean;
  error: string | null;
  requestLocation: () => void;
}

export const useLocation = (): UseLocationReturn => {
  const [location, setLocation] = useState<Location | null>(() => {
    // Check if location is stored in localStorage
    const stored = localStorage.getItem('userLocation');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    setLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const newLocation: Location = {
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        };
        setLocation(newLocation);
        // Store in localStorage
        localStorage.setItem('userLocation', JSON.stringify(newLocation));
        setLoading(false);
      },
      (err) => {
        let errorMessage = 'Failed to get your location';

        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Please enable location access in your browser settings.';
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = 'Location information is unavailable.';
            break;
          case err.TIMEOUT:
            errorMessage = 'Location request timed out.';
            break;
        }

        setError(errorMessage);
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    );
  };

  return { location, loading, error, requestLocation };
};
