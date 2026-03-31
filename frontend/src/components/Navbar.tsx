import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ChevronDown, Gavel, LogOut, User } from 'lucide-react';

// ── Nav data ──────────────────────────────────────────────────────────────────

const EVIDENCE_ITEMS: { label: string; to: string | null }[] = [
  { label: 'Photo Documents', to: '/photos/documents' },
  { label: 'Email Threads',   to: '/emails/threads' },
  { label: 'Events',          to: null },
  { label: 'PDFs',            to: null },
  { label: 'Library',         to: null },
];

const MANAGEMENT_ITEMS: { label: string; to: string | null }[] = [
  { label: 'Protagonists', to: null },
];

// ── Dropdown ──────────────────────────────────────────────────────────────────

interface DropdownItem { label: string; to: string | null }

function NavDropdown({
  label,
  items,
  activePrefixes,
}: {
  label: string;
  items: DropdownItem[];
  activePrefixes: string[];
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const isActive = activePrefixes.some(p => location.pathname.startsWith(p));

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Close on route change
  useEffect(() => { setOpen(false); }, [location.pathname]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-md transition-colors
          ${isActive
            ? 'text-primary bg-primary/5'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
      >
        {label}
        <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-150 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute left-0 top-full mt-1 w-52 bg-white border border-slate-200 rounded-md shadow-lg py-1 z-50">
          {items.map(item =>
            item.to ? (
              <Link
                key={item.label}
                to={item.to}
                className={`block px-4 py-2 text-sm transition-colors
                  ${location.pathname.startsWith(item.to)
                    ? 'bg-primary/5 text-primary font-medium'
                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                  }`}
              >
                {item.label}
              </Link>
            ) : (
              <span
                key={item.label}
                className="flex items-center justify-between px-4 py-2 text-sm text-slate-400 cursor-not-allowed select-none"
              >
                {item.label}
                <span className="text-xs font-normal bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded">soon</span>
              </span>
            )
          )}
        </div>
      )}
    </div>
  );
}

// ── Navbar ────────────────────────────────────────────────────────────────────

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const displayName = user
    ? (user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.email)
    : '';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center gap-6">

        {/* Brand */}
        <Link to="/" className="flex items-center gap-2 shrink-0 mr-2">
          <Gavel className="h-5 w-5 text-primary" />
          <span className="text-base font-bold tracking-tight text-slate-900">Court V2</span>
        </Link>

        {/* Primary nav */}
        <nav className="flex items-center gap-1">
          <Link
            to="/"
            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors
              ${location.pathname === '/'
                ? 'text-primary bg-primary/5'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
          >
            Home
          </Link>

          <NavDropdown
            label="Evidence"
            items={EVIDENCE_ITEMS}
            activePrefixes={['/photos', '/emails']}
          />

          <NavDropdown
            label="Management"
            items={MANAGEMENT_ITEMS}
            activePrefixes={['/protagonists']}
          />
        </nav>

        {/* Right side — user identity + logout */}
        <div className="ml-auto flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <User className="h-4 w-4 text-slate-400 shrink-0" />
              <span>
                Logged in as: <span className="font-medium text-slate-800">{displayName}</span>
              </span>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm font-medium text-red-500 hover:text-red-600 transition-colors px-2 py-1.5 rounded-md hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            Log Out
          </button>
        </div>

      </div>
    </header>
  );
}
