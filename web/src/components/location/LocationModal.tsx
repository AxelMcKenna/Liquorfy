import { useState, useEffect } from 'react';
import { MapPin, Navigation, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useLocationContext } from '@/contexts/LocationContext';
import { StoreMap } from '@/components/stores/StoreMap';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { reverseGeocode, formatLocationString } from '@/lib/geocoding';

type Step = 'initial' | 'auto-success' | 'manual-map';

export const LocationModal = () => {
  const {
    location,
    radiusKm,
    loading,
    error,
    isLocationModalOpen,
    closeLocationModal,
    requestAutoLocation,
    setManualLocation,
    setRadiusKm,
    isLocationSet,
  } = useLocationContext();

  const [step, setStep] = useState<Step>('initial');
  const [tempRadius, setTempRadius] = useState(radiusKm);
  const [tempLocation, setTempLocation] = useState(location);
  const [locationAddress, setLocationAddress] = useState<string>('');

  // Reset state when modal opens
  useEffect(() => {
    if (isLocationModalOpen) {
      if (isLocationSet && location) {
        // User is changing existing location
        setStep('auto-success');
        setTempLocation(location);
        setTempRadius(radiusKm);
      } else {
        // First time setting location
        setStep('initial');
        setTempRadius(radiusKm);
      }
    }
  }, [isLocationModalOpen, isLocationSet, location, radiusKm]);

  // Fetch address when location changes
  useEffect(() => {
    if (location) {
      reverseGeocode(location).then((result) => {
        if (result) {
          setLocationAddress(formatLocationString(result, location));
        } else {
          setLocationAddress(`${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`);
        }
      });
    }
  }, [location]);

  const handleAutoLocation = async () => {
    try {
      await requestAutoLocation();
      setStep('auto-success');
    } catch (err) {
      // Error is already handled in context, just move to manual step
      setStep('manual-map');
    }
  };

  const handleManualMode = () => {
    setStep('manual-map');
    // Initialize temp location to NZ center if no location set
    if (!tempLocation) {
      setTempLocation({ lat: -41.2924, lon: 174.7787 });
    }
  };

  const handleLocationChange = async (lat: number, lon: number) => {
    setTempLocation({ lat, lon });
    // Fetch address for the new location
    const result = await reverseGeocode({ lat, lon });
    if (result) {
      setLocationAddress(formatLocationString(result, { lat, lon }));
    } else {
      setLocationAddress(`${lat.toFixed(4)}, ${lon.toFixed(4)}`);
    }
  };

  const handleConfirmManual = () => {
    if (tempLocation) {
      // Pass radius along with location to avoid race condition
      setManualLocation(tempLocation.lat, tempLocation.lon, tempRadius);
      closeLocationModal();
      toast.success("Location set", {
        description: `Finding products within ${tempRadius}km`,
        duration: 3000,
      });
    }
  };

  const handleConfirmAuto = () => {
    setRadiusKm(tempRadius);
    closeLocationModal();
    toast.success("Location updated", {
      description: `Search radius set to ${tempRadius}km`,
      duration: 3000,
    });
  };

  const canClose = isLocationSet;

  return (
    <Dialog open={isLocationModalOpen} onOpenChange={canClose ? closeLocationModal : undefined}>
      <DialogContent
        className={`sm:max-w-[600px] ${!canClose ? '[&>button]:hidden' : ''}`}
        onPointerDownOutside={(e) => !canClose && e.preventDefault()}
        onEscapeKeyDown={(e) => !canClose && e.preventDefault()}
      >
        {step === 'initial' && (
          <>
            <DialogHeader>
              <DialogTitle>Set Your Location</DialogTitle>
              <DialogDescription>
                To show you products from nearby stores, we need your location.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <Button
                onClick={handleAutoLocation}
                disabled={loading}
                className="w-full h-14 text-lg"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Getting location...
                  </>
                ) : (
                  <>
                    <Navigation className="w-5 h-5 mr-2" />
                    Use My Location
                  </>
                )}
              </Button>

              <Button
                onClick={handleManualMode}
                variant="outline"
                className="w-full h-14 text-lg"
                size="lg"
                disabled={loading}
              >
                <MapPin className="w-5 h-5 mr-2" />
                Set Location on Map
              </Button>
            </div>
          </>
        )}

        {step === 'auto-success' && location && (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <CheckCircle2 className="w-6 h-6 text-green-600" />
                Location Set
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-6 py-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                <p className="text-sm text-green-800 mb-1">Using your current location</p>
                <p className="text-sm font-medium text-green-900">
                  {locationAddress || 'Loading address...'}
                </p>
                <p className="text-xs text-green-700 mt-1">
                  {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                </p>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Search Radius: {tempRadius}km
                </label>
                <Slider
                  value={[tempRadius]}
                  onValueChange={(value) => setTempRadius(value[0])}
                  min={5}
                  max={50}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>5km</span>
                  <span>50km</span>
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('manual-map')} className="flex-1">
                  Adjust Manually
                </Button>
                <Button onClick={handleConfirmAuto} className="flex-1">
                  Continue
                </Button>
              </div>
            </div>
          </>
        )}

        {step === 'manual-map' && (
          <>
            <DialogHeader>
              <DialogTitle>Set Location on Map</DialogTitle>
              <DialogDescription>
                Drag the pin to your approximate location
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {error && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div className="border rounded-lg overflow-hidden h-[400px]">
                <StoreMap
                  userLocation={tempLocation || { lat: -41.2924, lon: 174.7787 }}
                  stores={[]}
                  onLocationChange={handleLocationChange}
                  isDraggable={true}
                  radiusKm={tempRadius}
                />
              </div>

              {tempLocation && (
                <div className="text-center">
                  <p className="text-sm font-medium text-primary-gray">
                    {locationAddress || 'Loading address...'}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {tempLocation.lat.toFixed(4)}, {tempLocation.lon.toFixed(4)}
                  </p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Search Radius: {tempRadius}km
                </label>
                <Slider
                  value={[tempRadius]}
                  onValueChange={(value) => setTempRadius(value[0])}
                  min={5}
                  max={50}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>5km</span>
                  <span>50km</span>
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="outline" onClick={() => setStep('initial')} className="flex-1">
                  Back
                </Button>
                <Button onClick={handleConfirmManual} className="flex-1">
                  Confirm Location
                </Button>
              </div>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};
