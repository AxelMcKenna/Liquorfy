import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { InlineAlert } from '@/components/ui/inline-alert';
import { AuthCardHeader } from '@/components/auth/AuthCardHeader';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { supabase } from '@/lib/supabase';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email is required.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/auth/callback`,
      });
      if (resetError) throw resetError;
      setSent(true);
    } catch (err: any) {
      const msg = err?.message?.toLowerCase() ?? '';
      if (msg.includes('rate limit') || msg.includes('too many requests')) {
        setError('Too many attempts. Please wait a moment and try again.');
      } else {
        // Don't reveal whether the email exists - always show success
        setSent(true);
      }
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <AuthLayout backTo="/login" cardClassName="text-center">
        <AuthCardHeader icon={Mail} title="Check your email" />
        <p className="text-sm text-muted-foreground">
          If an account exists for <span className="font-medium text-foreground">{email}</span>, we've sent a password reset link. Check your inbox and spam folder.
        </p>
        <Button variant="outline" className="w-full" asChild>
          <Link to="/login">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Sign In
          </Link>
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout backTo="/login">
      <AuthCardHeader
        title="Reset your password"
        description="Enter your email and we'll send you a reset link"
      />

      {error && <InlineAlert variant="error">{error}</InlineAlert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError(''); }}
            className={error ? 'border-red-400 focus-visible:ring-red-400' : ''}
            required
            disabled={loading}
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </Button>
      </form>

      <p className="text-sm text-center text-muted-foreground">
        Remember your password?{' '}
        <Link to="/login" className="text-primary font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
};

export default ForgotPasswordPage;
