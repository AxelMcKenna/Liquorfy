import { ReactNode } from 'react';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface AuthLayoutProps {
  children: ReactNode;
  backTo?: string | 'history';
  cardClassName?: string;
}

export function AuthLayout({
  children,
  backTo = 'history',
  cardClassName,
}: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader backTo={backTo} />
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <Card className={cn('w-full max-w-sm p-8 space-y-6', cardClassName)}>
          {children}
        </Card>
      </main>
      <Footer />
    </div>
  );
}
