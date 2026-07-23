import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { InlineAlert } from '@/components/ui/inline-alert';
import { AuthCardHeader } from '@/components/auth/AuthCardHeader';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { supabase } from '@/lib/supabase';
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
    <AuthLayout>
      <AuthCardHeader
        icon={Lock}
        title="Set new password"
        description="Choose a new password for your account"
      />

      {errors.form && <InlineAlert variant="error">{errors.form}</InlineAlert>}

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
    </AuthLayout>
  );
};

export default ResetPasswordPage;
