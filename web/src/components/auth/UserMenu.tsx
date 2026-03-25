import { useState } from 'react';
import { LogOut, User, Eye, Settings, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';

export const UserMenu = () => {
  const { user, signOut, deleteAccount } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  if (!user) return null;

  const rawName = user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'Account';
  const firstName = rawName.split(' ')[0];
  const displayName = firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
    } catch {
      setDeleting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors"
      >
        <User className="w-4 h-4 text-white" />
        <span className="text-sm font-medium text-white hidden sm:block max-w-[140px] truncate">
          {displayName}
        </span>
      </button>

      {menuOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setMenuOpen(false)}
          />
          <div className="absolute right-0 top-full mt-1 w-56 bg-white rounded-lg shadow-lg border z-50 py-1">
            <a
              href="/watchlist"
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50"
              onClick={() => setMenuOpen(false)}
            >
              <Eye className="w-4 h-4" />
              Watchlist
            </a>
            <a
              href="/settings"
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50"
              onClick={() => setMenuOpen(false)}
            >
              <Settings className="w-4 h-4" />
              Settings
            </a>
            <button
              onClick={async () => {
                setMenuOpen(false);
                await signOut();
              }}
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50 w-full text-left"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
            <hr className="my-1" />
            <button
              onClick={() => {
                setMenuOpen(false);
                setConfirmDelete(true);
              }}
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-red-50 text-red-600 w-full text-left"
            >
              <Trash2 className="w-4 h-4" />
              Delete Account
            </button>
          </div>
        </>
      )}

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
  );
};
