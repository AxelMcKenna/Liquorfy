import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { InlineAlert } from '@/components/ui/inline-alert';
import { AuthCardHeader } from '@/components/auth/AuthCardHeader';
import { AuthDivider } from '@/components/auth/AuthDivider';
import { OAuthButtons } from '@/components/auth/OAuthButtons';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase';
import { toast } from 'sonner';

const RegisterPage = () => {
  const { user, signUp, signInWithGoogle, signInWithApple } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    form?: string;
  }>({});

  if (user) {
    return <Navigate to="/settings" replace />;
  }

  const validate = (): boolean => {
    const next: typeof errors = {};
    if (!name.trim()) {
      next.name = 'Name is required.';
    }
    if (!email.trim()) {
      next.email = 'Email is required.';
    }
    if (!password) {
      next.password = 'Password is required.';
    } else if (password.length < 6) {
      next.password = 'Password must be at least 6 characters.';
    }
    if (!confirmPassword) {
      next.confirmPassword = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      next.confirmPassword = 'Passwords do not match.';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const clearField = (field: keyof typeof errors) => {
    setErrors((p) => ({ ...p, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await signUp(email.trim(), password, name.trim());
      setEmailSent(true);
    } catch (err: any) {
      const msg = err?.message?.toLowerCase() ?? '';
      if (msg.includes('already registered') || msg.includes('already been registered')) {
        setErrors({ email: 'This email is already registered. Try signing in instead.' });
      } else if (msg.includes('valid email') || msg.includes('invalid')) {
        setErrors({ email: 'Please enter a valid email address.' });
      } else if (msg.includes('password') && msg.includes('weak')) {
        setErrors({ password: 'Password is too weak. Use a mix of letters, numbers and symbols.' });
      } else if (msg.includes('too many requests') || msg.includes('rate limit')) {
        setErrors({ form: 'Too many attempts. Please wait a moment and try again.' });
      } else {
        setErrors({ form: 'Could not create account. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const oauthTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => { if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current); };
  }, []);

  const startOAuthTimeout = () => {
    oauthTimerRef.current = window.setTimeout(() => {
      setLoading(false);
      setErrors({ form: 'Sign-up took too long. Please try again.' });
    }, 15000);
  };

  const handleGoogle = async () => {
    setLoading(true);
    setErrors({});
    startOAuthTimeout();
    try { await signInWithGoogle(); } catch { setLoading(false); if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current); }
  };

  const handleApple = async () => {
    setLoading(true);
    setErrors({});
    startOAuthTimeout();
    try { await signInWithApple(); } catch { setLoading(false); if (oauthTimerRef.current) window.clearTimeout(oauthTimerRef.current); }
  };

  const passwordStrength = useMemo(() => {
    if (!password) return { score: 0, label: '', color: '' };
    let score = 0;
    if (password.length >= 6) score++;
    if (password.length >= 10) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score <= 1) return { score: 1, label: 'Weak', color: 'bg-red-400' };
    if (score <= 2) return { score: 2, label: 'Fair', color: 'bg-amber-400' };
    if (score <= 3) return { score: 3, label: 'Good', color: 'bg-yellow-400' };
    if (score === 4) return { score: 4, label: 'Strong', color: 'bg-green-400' };
    return { score: 5, label: 'Very strong', color: 'bg-primary' };
  }, [password]);

  const fieldClass = (field: keyof typeof errors) =>
    errors[field] ? 'border-red-400 focus-visible:ring-red-400' : '';

  const [resendCooldown, setResendCooldown] = useState(0);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = window.setTimeout(() => setResendCooldown((c) => c - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [resendCooldown]);

  const handleResend = useCallback(async () => {
    setResending(true);
    try {
      const { error: resendError } = await supabase.auth.resend({
        type: 'signup',
        email: email.trim(),
        options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
      });
      if (resendError) throw resendError;
      toast.success('Confirmation email resent');
      setResendCooldown(60);
    } catch {
      toast.error('Could not resend email. Please try again later.');
    } finally {
      setResending(false);
    }
  }, [email]);

  if (emailSent) {
    return (
      <AuthLayout backTo="/" cardClassName="text-center">
        <AuthCardHeader icon={Mail} title="Check your email" />
        <p className="text-sm text-muted-foreground">
          We've sent a confirmation link to <span className="font-medium text-foreground">{email}</span>. Please check your inbox and click the link to activate your account.
        </p>
        <div className="space-y-3">
          <Button
            variant="ghost"
            size="sm"
            className="text-primary"
            onClick={handleResend}
            disabled={resending || resendCooldown > 0}
          >
            {resending
              ? 'Sending...'
              : resendCooldown > 0
                ? `Resend email (${resendCooldown}s)`
                : 'Resend confirmation email'}
          </Button>
          <p className="text-xs text-muted-foreground">
            Also check your spam folder if you don't see it.
          </p>
        </div>
        <Button variant="outline" className="w-full" onClick={() => navigate('/login')}>
          Go to Sign In
        </Button>
        <button
          onClick={() => navigate('/explore')}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Continue browsing
        </button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout cardClassName="p-6 space-y-4">
      <AuthCardHeader
        title="Create an account"
        description="Sign up to set price alerts and save preferences"
      />

      {errors.form && <InlineAlert variant="error">{errors.form}</InlineAlert>}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => { setName(e.target.value); clearField('name'); }}
            className={fieldClass('name')}
            required
            disabled={loading}
          />
          {errors.name && <p className="text-xs text-red-600">{errors.name}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); clearField('email'); }}
            className={fieldClass('email')}
            required
            disabled={loading}
          />
          {errors.email && <p className="text-xs text-red-600">{errors.email}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="At least 6 characters"
            value={password}
            onChange={(e) => { setPassword(e.target.value); clearField('password'); }}
            className={fieldClass('password')}
            required
            disabled={loading}
          />
          {password && (
            <div className="space-y-1">
              <div className="flex gap-1 h-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-colors ${
                      i <= passwordStrength.score ? passwordStrength.color : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-muted-foreground">{passwordStrength.label}</p>
            </div>
          )}
          {errors.password && <p className="text-xs text-red-600">{errors.password}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="confirm-password">Confirm Password</Label>
          <Input
            id="confirm-password"
            type="password"
            placeholder="Confirm your password"
            value={confirmPassword}
            onChange={(e) => { setConfirmPassword(e.target.value); clearField('confirmPassword'); }}
            className={fieldClass('confirmPassword')}
            required
            disabled={loading}
          />
          {errors.confirmPassword && <p className="text-xs text-red-600">{errors.confirmPassword}</p>}
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          Create Account
        </Button>
      </form>

      <AuthDivider />
      <OAuthButtons disabled={loading} onGoogle={handleGoogle} onApple={handleApple} />

      <p className="text-xs text-center text-muted-foreground leading-relaxed">
        By creating an account, you agree to our{' '}
        <Link to="/terms" className="text-primary hover:underline">Terms of Service</Link>
        {' '}and{' '}
        <Link to="/privacy" className="text-primary hover:underline">Privacy Policy</Link>.
      </p>

      <p className="text-sm text-center text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="text-primary font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
};

export default RegisterPage;
