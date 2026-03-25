import { ReactNode, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginDialog } from './LoginDialog';

export const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user, loading } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <p className="text-lg text-muted-foreground mb-4">
            Sign in to access this page
          </p>
          <LoginDialog
            open={loginOpen || true}
            onOpenChange={setLoginOpen}
          />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
