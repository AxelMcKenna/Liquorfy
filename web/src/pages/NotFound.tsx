import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';

const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader backTo="/" />

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="text-center space-y-4">
          <h1 className="text-6xl font-serif font-semibold text-primary">404</h1>
          <p className="text-lg text-muted-foreground">Page not found</p>
          <Button asChild>
            <Link to="/">Back to Home</Link>
          </Button>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default NotFoundPage;
