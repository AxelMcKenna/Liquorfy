import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, Navigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { InlineAlert } from '@/components/ui/inline-alert';
import { AuthCardHeader } from '@/components/auth/AuthCardHeader';
import { AuthDivider } from '@/components/auth/AuthDivider';
import { OAuthButtons } from '@/components/auth/OAuthButtons';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { useAuth } from '@/contexts/AuthContext';

const LoginPage = () => {
  const { user, signInWithPassword, signInWithGoogle, signInWithApple } = useAuth();
  const navigate = useNavigate();
  const locationState = useLocation();
  const redirectTo = (locationState.state as { from?: string })?.from || '/';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string; form?: string }>({});
  const oauthTimerRef = useRef<number | null>(null);

  // Clear OAuth timeout on unmount (successful redirect)
  useEffect(() => {
    return () => {
      if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current);
    };
  }, []);

  if (user) {
    return <Navigate to="/settings" replace />;
  }

  const validate = (): boolean => {
    const next: typeof errors = {};
    if (!email.trim()) {
      next.email = 'Email is required.';
    }
    if (!password) {
      next.password = 'Password is required.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await signInWithPassword(email.trim(), password);
      navigate(redirectTo, { replace: true });
    } catch (err: any) {
      const msg = err?.message?.toLowerCase() ?? '';
      if (msg.includes('invalid login credentials') || msg.includes('invalid_credentials')) {
        setErrors({ form: 'Invalid email or password.' });
      } else if (msg.includes('email not confirmed')) {
        setErrors({ form: 'Please confirm your email before signing in. Check your inbox.' });
      } else if (msg.includes('too many requests') || msg.includes('rate limit')) {
        setErrors({ form: 'Too many attempts. Please wait a moment and try again.' });
      } else {
        setErrors({ form: 'Something went wrong. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const startOAuthTimeout = () => {
    oauthTimerRef.current = window.setTimeout(() => {
      setLoading(false);
      setErrors({ form: 'Sign-in took too long. Please try again.' });
    }, 15000);
  };

  const persistRedirect = () => {
    if (redirectTo && redirectTo !== '/') {
      sessionStorage.setItem('auth_redirect', redirectTo);
    }
  };

  const handleGoogle = async () => {
    setLoading(true);
    setErrors({});
    persistRedirect();
    startOAuthTimeout();
    try { await signInWithGoogle(); } catch { setLoading(false); if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current); }
  };

  const handleApple = async () => {
    setLoading(true);
    setErrors({});
    persistRedirect();
    startOAuthTimeout();
    try { await signInWithApple(); } catch { setLoading(false); if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current); }
  };

  return (
    <AuthLayout>
      <AuthCardHeader title="Welcome back" description="Sign in to your account" />

      {errors.form && <InlineAlert variant="error">{errors.form}</InlineAlert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: undefined, form: undefined })); }}
            className={errors.email ? 'border-red-400 focus-visible:ring-red-400' : ''}
            required
            disabled={loading}
          />
          {errors.email && <p className="text-xs text-red-600">{errors.email}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="Your password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: undefined, form: undefined })); }}
            className={errors.password ? 'border-red-400 focus-visible:ring-red-400' : ''}
            required
            disabled={loading}
          />
          {errors.password && <p className="text-xs text-red-600">{errors.password}</p>}
          <div className="text-right">
            <Link to="/forgot-password" className="text-xs text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          Sign In
        </Button>
      </form>

      <AuthDivider />
      <OAuthButtons disabled={loading} onGoogle={handleGoogle} onApple={handleApple} />

      <p className="text-xs text-center text-muted-foreground leading-relaxed">
        By signing in, you agree to our{' '}
        <Link to="/terms" className="text-primary hover:underline">Terms of Service</Link>
        {' '}and{' '}
        <Link to="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
      </p>

      <p className="text-sm text-center text-muted-foreground">
        Don't have an account?{' '}
        <Link to="/register" className="text-primary font-medium hover:underline">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
};

export default LoginPage;
