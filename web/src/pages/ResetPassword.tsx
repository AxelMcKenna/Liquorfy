import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { supabase } from '@/lib/supabase';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { toast } from 'sonner';

const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ password?: string; confirm?: string; form?: string }>({});

  const validate = (): boolean => {
    const next: typeof errors = {};
    if (!password) {
      next.password = 'Password is required.';
    } else if (password.length < 6) {
      next.password = 'Password must be at least 6 characters.';
    }
    if (!confirmPassword) {
      next.confirm = 'Please confirm your password.';
    } else if (password !== confirmPassword) {
      next.confirm = 'Passwords do not match.';
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
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw error;
      toast.success('Password updated successfully');
      navigate('/settings', { replace: true });
    } catch (err: any) {
      const msg = err?.message?.toLowerCase() ?? '';
      if (msg.includes('same password') || msg.includes('different password')) {
        setErrors({ password: 'New password must be different from your current password.' });
      } else if (msg.includes('weak')) {
        setErrors({ password: 'Password is too weak. Use a mix of letters, numbers and symbols.' });
      } else if (msg.includes('session') || msg.includes('not authenticated')) {
        setErrors({ form: 'Your reset link has expired. Please request a new one.' });
      } else {
        setErrors({ form: 'Could not update password. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <PageHeader />

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-lg border shadow-md p-8 space-y-6">
          <div className="text-center">
            <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Lock className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-2xl font-serif font-semibold tracking-tight">
              Set new password
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              Choose a new password for your account
            </p>
          </div>

          {errors.form && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-3">
              {errors.form}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">New Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: undefined })); }}
                className={errors.password ? 'border-red-400 focus-visible:ring-red-400' : ''}
                required
                disabled={loading}
              />
              {errors.password && <p className="text-xs text-red-600">{errors.password}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm Password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => { setConfirmPassword(e.target.value); setErrors((p) => ({ ...p, confirm: undefined })); }}
                className={errors.confirm ? 'border-red-400 focus-visible:ring-red-400' : ''}
                required
                disabled={loading}
              />
              {errors.confirm && <p className="text-xs text-red-600">{errors.confirm}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Updating...' : 'Update Password'}
            </Button>
          </form>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default ResetPasswordPage;
