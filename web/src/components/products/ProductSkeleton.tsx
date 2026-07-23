import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const ProductSkeleton = () => {
  return (
    <Card className="h-full overflow-hidden bg-card" aria-hidden="true">
      <div className="w-full aspect-[4/3] sm:aspect-square bg-secondary/70 skeleton-shimmer" />

      <CardContent className="p-3 flex-1 space-y-2">
        <div className="space-y-1.5">
          <Skeleton className="h-3.5 w-full bg-secondary" />
          <Skeleton className="h-3.5 w-3/4 bg-secondary" />
          <Skeleton className="h-3 w-2/5 bg-secondary" />
        </div>
        <Skeleton className="h-3 w-4/5 bg-secondary" />
        <Skeleton className="h-6 w-20 bg-secondary" />
        <Skeleton className="h-3 w-16 bg-secondary" />
        <Skeleton className="h-3 w-24 bg-secondary" />
      </CardContent>
    </Card>
  );
};
