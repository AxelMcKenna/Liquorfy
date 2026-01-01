import { ReactNode, useEffect } from 'react';
import { useLocationContext } from '@/contexts/LocationContext';
import { LocationModal } from './LocationModal';

interface LocationGateProps {
  children: ReactNode;
}

export const LocationGate = ({ children }: LocationGateProps) => {
  const { isLocationSet, openLocationModal } = useLocationContext();

  useEffect(() => {
    // Open modal automatically if location is not set
    if (!isLocationSet) {
      openLocationModal();
    }
  }, [isLocationSet, openLocationModal]);

  return (
    <>
      <LocationModal />
      {children}
    </>
  );
};
