import { ElementType } from 'react';

interface AuthCardHeaderProps {
  title: string;
  description?: string;
  icon?: ElementType;
}

export function AuthCardHeader({
  title,
  description,
  icon: Icon,
}: AuthCardHeaderProps) {
  return (
    <div className="text-center">
      {Icon && (
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <Icon className="h-6 w-6 text-primary" aria-hidden="true" />
        </div>
      )}
      <h1 className="text-2xl font-serif font-semibold tracking-tight">{title}</h1>
      {description && (
        <p className="text-sm text-muted-foreground mt-2">{description}</p>
      )}
    </div>
  );
}
