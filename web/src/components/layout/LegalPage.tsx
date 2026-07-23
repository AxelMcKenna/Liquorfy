import { ReactNode } from 'react';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';

interface LegalPageProps {
  title: string;
  subtitle: ReactNode;
  children: ReactNode;
}

export function LegalPage({ title, subtitle, children }: LegalPageProps) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader backTo="/" />
      <main className="max-w-3xl mx-auto w-full px-4 py-12 flex-1">
        <h1 className="text-3xl font-semibold text-foreground mb-2">{title}</h1>
        <div className="text-sm text-muted-foreground mb-10">{subtitle}</div>
        <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}
