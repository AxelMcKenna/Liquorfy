import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface MapSurfaceProps {
  children: ReactNode;
  className?: string;
}

export function MapSurface({ children, className }: MapSurfaceProps) {
  return (
    <div className={cn('w-full h-[500px] rounded-lg overflow-hidden border border-border', className)}>
      {children}
    </div>
  );
}
