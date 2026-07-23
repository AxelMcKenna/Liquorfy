import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type InlineAlertVariant = 'info' | 'error' | 'warning' | 'success';

interface InlineAlertProps {
  children: ReactNode;
  variant?: InlineAlertVariant;
  className?: string;
}

const variantClasses: Record<InlineAlertVariant, string> = {
  info: 'border-primary/20 bg-primary/5 text-foreground',
  error: 'border-destructive/20 bg-destructive/10 text-destructive',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  success: 'border-primary/20 bg-primary/10 text-primary',
};

export function InlineAlert({
  children,
  variant = 'info',
  className,
}: InlineAlertProps) {
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={cn('rounded-lg border px-4 py-3 text-sm', variantClasses[variant], className)}
    >
      {children}
    </div>
  );
}
