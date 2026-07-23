import { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import { LogOut, User, Eye, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export const UserMenu = () => {
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  if (!user) return null;

  const rawName = user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'Account';
  const firstName = rawName.split(' ')[0];
  const displayName = firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();

  const rect = buttonRef.current?.getBoundingClientRect();
  const dropdownStyle = rect
    ? { top: rect.bottom + 4, right: Math.max(8, window.innerWidth - rect.right) }
    : { top: 0, right: 8 };

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setMenuOpen(!menuOpen)}
        aria-label="Account menu"
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        className="flex min-h-11 items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors"
      >
        <User className="w-4 h-4 text-white" />
        <span className="text-sm font-medium text-white hidden sm:block max-w-[140px] truncate">
          {displayName}
        </span>
      </button>

      {menuOpen && createPortal(
        <>
          <button
            type="button"
            aria-label="Close account menu"
            className="fixed inset-0 z-[9998]"
            onClick={() => setMenuOpen(false)}
          />
          <div
            role="menu"
            className="fixed w-48 sm:w-56 bg-white rounded-lg shadow-lg border z-[9999] py-1"
            style={dropdownStyle}
          >
            <Link
              to="/watchlist"
              role="menuitem"
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50"
              onClick={() => setMenuOpen(false)}
            >
              <Eye className="w-4 h-4" />
              Watchlist
            </Link>
            <Link
              to="/settings"
              role="menuitem"
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50"
              onClick={() => setMenuOpen(false)}
            >
              <Settings className="w-4 h-4" />
              Settings
            </Link>
            <button
              role="menuitem"
              onClick={async () => {
                setMenuOpen(false);
                await signOut();
              }}
              className="flex items-center gap-2 px-4 py-2.5 text-sm hover:bg-gray-50 w-full text-left"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </>,
        document.body
      )}
    </div>
  );
};
