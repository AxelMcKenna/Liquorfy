import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const ProductSkeleton = () => {
  return (
    <Card className="h-full flex flex-col overflow-hidden border bg-card">
      {/* Animated pulse bar */}
      <div className="h-1 bg-primary/20 animate-pulse" />

      {/* Image skeleton - Light background */}
      <div className="w-full aspect-square bg-gray-200 animate-pulse" />

      <CardContent className="p-4 flex-1 space-y-3">
        {/* Title and brand */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-full bg-secondary/50" />
          <Skeleton className="h-4 w-3/4 bg-secondary/50" />
        </div>
        {/* Store */}
        <Skeleton className="h-3 w-1/2 bg-secondary/50" />
        {/* Price */}
        <Skeleton className="h-8 w-24 bg-secondary/50" />
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Skeleton className="h-10 w-full bg-secondary/50" />
      </CardFooter>
    </Card>
  );
};
