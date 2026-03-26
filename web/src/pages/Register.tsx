import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
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
    navigate('/settings', { replace: true });
    return null;
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

  const handleGoogle = async () => {
    setLoading(true);
    setErrors({});
    try { await signInWithGoogle(); } catch { setLoading(false); }
  };

  const handleApple = async () => {
    setLoading(true);
    setErrors({});
    try { await signInWithApple(); } catch { setLoading(false); }
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

  if (emailSent) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        <PageHeader backTo="/" />
        <main className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-sm bg-white rounded-lg border shadow-md p-8 space-y-6 text-center">
            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
              <Mail className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-2xl font-serif font-semibold tracking-tight">
              Check your email
            </h2>
            <p className="text-sm text-muted-foreground">
              We've sent a confirmation link to <span className="font-medium text-foreground">{email}</span>. Please check your inbox and click the link to activate your account.
            </p>
            <p className="text-xs text-muted-foreground">
              Didn't receive it? Check your spam folder or try again in a few minutes.
            </p>
            <Button variant="outline" className="w-full" onClick={() => navigate('/login')}>
              Go to Sign In
            </Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader />

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-lg border shadow-md p-6 space-y-4">
          <div className="text-center">
            <h2 className="text-2xl font-serif font-semibold tracking-tight">
              Create an account
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Sign up to set price alerts and save preferences
            </p>
          </div>

          {errors.form && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-3">
              {errors.form}
            </div>
          )}

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
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              Create Account
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-muted-foreground">or</span>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Button variant="outline" className="w-full" onClick={handleGoogle} disabled={loading}>
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Continue with Google
            </Button>
            <Button variant="outline" className="w-full" onClick={handleApple} disabled={loading}>
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
              </svg>
              Continue with Apple
            </Button>
          </div>

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
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default RegisterPage;
