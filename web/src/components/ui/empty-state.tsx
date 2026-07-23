import { ElementType, ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: ElementType;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('text-center py-16', className)}>
      <Icon className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" aria-hidden="true" />
      <p className="text-foreground font-medium">{title}</p>
      {description && (
        <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
