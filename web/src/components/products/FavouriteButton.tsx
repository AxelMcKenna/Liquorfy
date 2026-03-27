import { Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface FavouriteButtonProps {
  isFavourite: boolean;
  onToggle: () => void;
  className?: string;
  size?: 'sm' | 'default';
}

export const FavouriteButton = ({
  isFavourite,
  onToggle,
  className,
  size = 'sm',
}: FavouriteButtonProps) => {
  return (
    <Button
      variant="ghost"
      size={size === 'sm' ? 'icon' : 'default'}
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
        if (isFavourite) {
          toast('Removed from watchlist', {
            duration: 4000,
            action: {
              label: 'Undo',
              onClick: () => onToggle(),
            },
          });
        } else {
          toast('Added to watchlist', { duration: 2000 });
        }
      }}
      className={cn(
        'rounded-full',
        isFavourite
          ? 'text-red-500 hover:text-red-600'
          : 'text-muted-foreground hover:text-red-500',
        className
      )}
      title={isFavourite ? 'Remove from favourites' : 'Add to favourites'}
    >
      <Heart
        className={cn('h-4 w-4', isFavourite && 'fill-current')}
      />
    </Button>
  );
};
