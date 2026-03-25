import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bell, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

const DISMISSED_KEY = 'liquorfy_signin_nudge_dismissed';

export const SignInNudge = () => {
  const { user } = useAuth();
  const [dismissed, setDismissed] = useState(() => {
    return sessionStorage.getItem(DISMISSED_KEY) === 'true';
  });

  if (user || dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem(DISMISSED_KEY, 'true');
  };

  return (
    <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <Bell className="h-4 w-4 text-primary flex-shrink-0" />
        <p className="text-sm text-foreground">
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
          {' '}to set price alerts and get notified when prices drop.
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={handleDismiss}
        className="flex-shrink-0 h-8 w-8 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
};
