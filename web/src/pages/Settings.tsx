import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AlertsList } from '@/components/alerts/AlertsList';

const SettingsPage = () => {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <header className="bg-primary border-b border-primary">
          <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-4">
            <Link to="/" className="text-white hover:text-white/80">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-lg font-semibold text-white">Settings</h1>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
          {/* Account info */}
          <section>
            <h2 className="text-lg font-serif font-semibold mb-3">Account</h2>
            <div className="bg-white rounded-lg border p-4">
              <p className="text-sm text-muted-foreground">
                Signed in as{' '}
                <strong>{user?.email || user?.user_metadata?.full_name || 'Unknown'}</strong>
              </p>
            </div>
          </section>

          {/* Alerts */}
          <section>
            <h2 className="text-lg font-serif font-semibold mb-3">Price Alerts</h2>
            <AlertsList />
          </section>
        </main>
      </div>
    </ProtectedRoute>
  );
};

export default SettingsPage;
