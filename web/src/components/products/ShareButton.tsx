import { Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface ShareButtonProps {
  productName: string;
  productId: string;
  className?: string;
}

export const ShareButton = ({ productName, productId, className }: ShareButtonProps) => {
  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const url = `${window.location.origin}/explore?q=${encodeURIComponent(productName)}`;

    if (navigator.share) {
      try {
        await navigator.share({ title: productName, text: `Check out ${productName} on Liquorfy`, url });
        return;
      } catch {
        // User cancelled or share failed — fall through to clipboard
      }
    }

    try {
      await navigator.clipboard.writeText(url);
      toast.success('Link copied to clipboard');
    } catch {
      toast.error('Failed to copy link');
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleShare}
      className={cn("rounded-full text-muted-foreground hover:text-primary", className)}
      title="Share product"
    >
      <Share2 className="h-4 w-4" />
    </Button>
  );
};
