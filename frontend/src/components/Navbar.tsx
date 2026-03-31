import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  ChevronDown, 
  Gavel, 
  LogOut, 
  User, 
  Image as ImageIcon, 
  Mail, 
  FileText, 
  Calendar, 
  MessageSquare, 
  Library as LibraryIcon,
  Search,
  Upload,
  Quote,
  LayoutList,
  Layers,
  PlusCircle,
  Clock,
  Briefcase,
  GitBranch,
  SearchCode,
  AlertTriangle,
  Settings,
  History
} from 'lucide-react';
import { cn } from '../lib/utils';

// ── Nav Types ────────────────────────────────────────────────────────────────

interface NavItem {
  label: string;
  to: string | null;
  icon?: React.ElementType;
  soon?: boolean;
}

interface NavSection {
  header?: string;
  items: NavItem[];
}

interface NavCategory {
  label: string;
  icon: React.ElementType;
  sections: NavSection[];
  activePrefixes: string[];
}

// ── Nav Data ─────────────────────────────────────────────────────────────────

const CATEGORIES: NavCategory[] = [
  {
    label: 'Case Manager',
    icon: Briefcase,
    activePrefixes: ['/cases'],
    sections: [
      {
        items: [
          { label: 'View All Cases', to: null, soon: true, icon: LayoutList },
          { label: 'Create New Case', to: null, soon: true, icon: PlusCircle },
          { label: 'Global Timeline', to: null, soon: true, icon: Clock },
        ]
      }
    ]
  },
  {
    label: 'Arguments',
    icon: GitBranch,
    activePrefixes: ['/arguments'],
    sections: [
      {
        items: [
          { label: 'View Narratives', to: null, soon: true, icon: LayoutList },
          { label: 'Create New Narrative', to: null, soon: true, icon: PlusCircle },
          { label: 'Grouped Narratives', to: null, soon: true, icon: Layers },
        ]
      }
    ]
  },
  {
    label: 'Photos & Evidence',
    icon: ImageIcon,
    activePrefixes: ['/photos', '/events'],
    sections: [
      {
        header: 'Photo Management',
        items: [
          { label: 'Upload Photo', to: null, soon: true, icon: Upload },
          { label: 'Photo List', to: null, soon: true, icon: LayoutList },
          { label: 'Photo Timeline', to: null, soon: true, icon: Clock },
          { label: 'Batch Process', to: null, soon: true, icon: Settings },
        ]
      },
      {
        header: 'Event Evidence',
        items: [
          { label: 'Events List', to: '/events', icon: Calendar },
        ]
      },
      {
        header: 'Document Evidence',
        items: [
          { label: 'Create Photo Doc', to: null, soon: true, icon: PlusCircle },
          { label: 'Photo Documents', to: '/photos/documents', icon: FileText },
        ]
      }
    ]
  },
  {
    label: 'Email Manager',
    icon: Mail,
    activePrefixes: ['/emails'],
    sections: [
      {
        header: 'Collection',
        items: [
          { label: 'Search Gmail', to: null, soon: true, icon: SearchCode },
          { label: 'Upload EML', to: '/emails/upload', icon: Upload },
        ]
      },
      {
        header: 'Saved Data',
        items: [
          { label: 'View Saved Threads', to: '/emails/threads', icon: LayoutList },
          { label: 'View All Quotes', to: null, soon: true, icon: Quote },
        ]
      }
    ]
  },
  {
    label: 'Document Manager',
    icon: LibraryIcon,
    activePrefixes: ['/documents'],
    sections: [
      {
        header: 'Library',
        items: [
          { label: 'View All Documents', to: null, soon: true, icon: LayoutList },
          { label: 'Create Document', to: null, soon: true, icon: PlusCircle },
          { label: 'Produced Docs', to: null, soon: true, icon: FileText },
        ]
      },
      {
        header: 'Analysis',
        items: [
          { label: 'Perjury Elements', to: null, soon: true, icon: AlertTriangle },
        ]
      }
    ]
  },
  {
    label: 'PDF Manager',
    icon: FileText,
    activePrefixes: ['/pdfs'],
    sections: [
      {
        items: [
          { label: 'View PDFs', to: '/pdfs', icon: LayoutList },
          { label: 'Upload PDF', to: null, soon: true, icon: Upload },
        ]
      }
    ]
  },
  {
    label: 'Google Chat',
    icon: MessageSquare,
    activePrefixes: ['/chats'],
    sections: [
      {
        items: [
          { label: 'Chat Stream', to: '/chats/stream', icon: MessageSquare },
          { label: 'Saved Sequences', to: '/chats/sequences', icon: Layers },
        ]
      }
    ]
  }
];

// ── Dropdown Component ────────────────────────────────────────────────────────

function NavDropdown({ category }: { category: NavCategory }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const isActive = category.activePrefixes.some(p => location.pathname.startsWith(p));

  // Auto-close on route change
  useEffect(() => { setOpen(false); }, [location.pathname]);

  return (
    <div 
      ref={ref} 
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        className={cn(
          "flex items-center gap-1.5 px-3 py-2 text-[13px] font-semibold rounded-md transition-all whitespace-nowrap",
          isActive 
            ? "text-primary bg-primary/5" 
            : "text-slate-600 hover:text-slate-900 hover:bg-slate-100",
          open && "bg-slate-100 text-slate-900"
        )}
      >
        <category.icon className="h-4 w-4" />
        {category.label}
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform duration-150", open && "rotate-180")} />
      </button>

      {open && (
        <div 
          className="absolute left-0 top-full pt-1 w-64 z-50 animate-in fade-in zoom-in-95 duration-100"
        >
          <div className="bg-white border border-slate-200 rounded-lg shadow-xl py-2">
            {category.sections.map((section, sIdx) => (
              <div key={sIdx}>
                {section.header && (
                  <div className="px-4 py-1.5 mt-1 text-[10px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-50 mb-1">
                    {section.header}
                  </div>
                )}
                {section.items.map(item => (
                  item.to ? (
                    <Link
                      key={item.label}
                      to={item.to}
                      className={cn(
                        "flex items-center gap-3 px-4 py-2 text-sm transition-colors mx-1 rounded-md",
                        location.pathname === item.to
                          ? "bg-primary/5 text-primary font-bold"
                          : "text-slate-700 hover:bg-slate-50 hover:text-slate-900"
                      )}
                    >
                      {item.icon && <item.icon className="h-4 w-4 opacity-60" />}
                      {item.label}
                    </Link>
                  ) : (
                    <div
                      key={item.label}
                      className="flex items-center justify-between px-4 py-2 text-sm text-slate-300 cursor-not-allowed select-none italic mx-1"
                    >
                      <div className="flex items-center gap-3">
                        {item.icon && <item.icon className="h-4 w-4 opacity-30" />}
                        {item.label}
                      </div>
                      {item.soon && <span className="text-[9px] font-bold bg-slate-50 text-slate-400 px-1.5 py-0.5 rounded uppercase border border-slate-100">Soon</span>}
                    </div>
                  )
                ))}
                {sIdx < category.sections.length - 1 && <div className="h-px bg-slate-100 my-1 mx-2" />}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Navbar Main ───────────────────────────────────────────────────────────────

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const displayName = user
    ? (user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.email)
    : '';

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-sm border-b-4 border-red-600 shadow-sm">
      <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center gap-2">

        {/* Brand */}
        <Link to="/" className="flex items-center gap-2 shrink-0 mr-4 group">
          <div className="bg-primary rounded-lg p-1.5 transition-transform group-hover:scale-110 shadow-sm">
            <Gavel className="h-5 w-5 text-white" />
          </div>
          <span className="text-[17px] font-black tracking-tighter text-slate-900 hidden xl:inline-block">
            COURT <span className="text-primary">V2</span>
          </span>
        </Link>

        {/* Primary nav */}
        <nav className="flex items-center gap-0.5 overflow-x-auto no-scrollbar py-1">
          <Link
            to="/"
            className={cn(
              "px-3 py-2 text-[13px] font-semibold rounded-md transition-colors",
              location.pathname === '/'
                ? "text-primary bg-primary/5"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            )}
          >
            Home
          </Link>

          {CATEGORIES.map(cat => (
            <NavDropdown key={cat.label} category={cat} />
          ))}

          <div className="h-4 w-px bg-slate-200 mx-2 shrink-0" />

          <Link
            to="/protagonists"
            className={cn(
              "flex items-center gap-1.5 px-3 py-2 text-[13px] font-semibold rounded-md transition-colors whitespace-nowrap",
              location.pathname.startsWith('/protagonists')
                ? "text-primary bg-primary/5"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            )}
          >
            <User className="h-4 w-4" />
            Protagonists
          </Link>
        </nav>

        {/* Right side — user identity + logout */}
        <div className="ml-auto flex items-center gap-3 shrink-0">
          {user && (
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-slate-50 rounded-full border border-slate-100 shadow-inner">
              <div className="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center">
                 <User className="h-3 w-3 text-primary" />
              </div>
              <span className="text-[12px] font-bold text-slate-700 max-w-[120px] truncate">{displayName}</span>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-red-500 hover:text-white transition-all px-3 py-1.5 rounded-md hover:bg-red-500 border border-red-200 hover:border-red-500 shadow-sm active:scale-95"
          >
            <LogOut className="h-3.5 w-3.5" />
            Logout
          </button>
        </div>

      </div>
    </header>
  );
}
