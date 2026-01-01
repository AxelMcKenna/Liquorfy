import { createContext, useContext, ReactNode } from 'react';
import { useCompare } from '@/hooks/useCompare';
import { Product } from '@/types';

interface CompareContextType {
  compare: Product[];
  sortedCompare: Product[];
  toggleCompare: (product: Product) => void;
  clearCompare: () => void;
  isAtLimit: boolean;
  canAddMore: boolean;
  compareCount: number;
  maxCompare: number;
}

const CompareContext = createContext<CompareContextType | undefined>(undefined);

export const CompareProvider = ({ children }: { children: ReactNode }) => {
  const compareState = useCompare();

  return (
    <CompareContext.Provider value={compareState}>
      {children}
    </CompareContext.Provider>
  );
};

export const useCompareContext = () => {
  const context = useContext(CompareContext);
  if (!context) {
    throw new Error('useCompareContext must be used within CompareProvider');
  }
  return context;
};
