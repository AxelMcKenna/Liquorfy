import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabase';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const getRedirect = () => {
      const stored = sessionStorage.getItem('auth_redirect');
      sessionStorage.removeItem('auth_redirect');
      return stored || '/';
    };

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') {
        navigate('/reset-password', { replace: true });
      } else if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        navigate(getRedirect(), { replace: true });
      }
    });

    // Fallback: if no auth event fires within 3s (e.g. session already established),
    // redirect so the user isn't stuck on a spinner forever.
    const fallback = setTimeout(() => navigate(getRedirect(), { replace: true }), 3000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(fallback);
    };
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-600">Signing you in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
