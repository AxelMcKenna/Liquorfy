import { Link } from 'react-router-dom';
import { LogOut, Trash2, BellRing, Heart } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { useNotificationPreferences } from '@/hooks/useNotificationPreferences';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';

const SettingsPage = () => {
  const { user, signOut, deleteAccount } = useAuth();
  const { prefs, updatePref } = useNotificationPreferences();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch {
      // handled by context
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
    } catch {
      setDeleting(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <PageHeader
          rightContent={
            <Link to="/watchlist" className="flex items-center justify-center h-8 w-8 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors">
              <Heart className="h-4 w-4" />
            </Link>
          }
        />

        <main className="max-w-5xl mx-auto px-4 py-8 space-y-8 flex-1 w-full">
          {/* Account info */}
          <section>
            <h2 className="text-lg font-serif font-semibold mb-3">Account</h2>
            <div className="bg-white rounded-lg border p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground break-all">
                Signed in as{' '}
                <strong>{user?.email || 'Unknown'}</strong>
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSignOut}
                className="text-muted-foreground hover:text-foreground gap-2 flex-shrink-0 self-start sm:self-auto"
              >
                <LogOut className="h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </section>

          {/* Notifications */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <BellRing className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-serif font-semibold">Notifications</h2>
            </div>
            <div className="bg-white rounded-lg border divide-y">
              <div className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium">Weekly deals email</p>
                  <p className="text-xs text-muted-foreground">Get the best deals near you every week</p>
                </div>
                <Switch
                  checked={prefs.weeklyDealsEmail}
                  onCheckedChange={(v) => {
                    updatePref('weeklyDealsEmail', v);
                    toast(v ? 'Weekly deals email enabled' : 'Weekly deals email disabled', { duration: 2000 });
                  }}
                />
              </div>
              <div className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium">Price drop alerts</p>
                  <p className="text-xs text-muted-foreground">Get notified when tracked products drop in price</p>
                </div>
                <Switch
                  checked={prefs.priceDropAlerts}
                  onCheckedChange={(v) => {
                    updatePref('priceDropAlerts', v);
                    toast(v ? 'Price drop alerts enabled' : 'Price drop alerts disabled', { duration: 2000 });
                  }}
                />
              </div>
            </div>
          </section>

          {/* Danger zone */}
          <section>
            <h2 className="text-lg font-serif font-semibold mb-3 text-destructive">Danger Zone</h2>
            <div className="bg-white rounded-lg border border-red-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium">Delete Account</p>
                <p className="text-xs text-muted-foreground">Permanently delete your account and all data.</p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setConfirmDelete(true)}
                className="flex-shrink-0 self-start sm:self-auto"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </div>
          </section>
        </main>

        <Footer />

        <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Delete Account</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-muted-foreground">
              This will permanently delete your account and all associated data
              (preferences, alerts). This action cannot be undone.
            </p>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setConfirmDelete(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete Account'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </ProtectedRoute>
  );
};

export default SettingsPage;
