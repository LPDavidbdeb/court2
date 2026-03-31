import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Briefcase, 
  FileText, 
  Mail, 
  LayoutDashboard, 
  LogOut,
  ChevronRight,
  Gavel,
  CalendarDays
} from 'lucide-react';
import { Button } from './ui/button';
import Navbar from './Navbar';

const SidebarItem = ({ icon: Icon, label, to, active }: any) => (
  <Link to={to}>
    <div className={`
      flex items-center gap-3 px-4 py-2 rounded-lg transition-colors
      ${active ? 'bg-primary text-primary-foreground' : 'text-slate-600 hover:bg-slate-100'}
    `}>
      <Icon className="h-5 w-5" />
      <span className="font-medium">{label}</span>
      {active && <ChevronRight className="ml-auto h-4 w-4" />}
    </div>
  </Link>
);

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col fixed inset-y-0 shadow-sm z-50">
        <div className="p-6 border-b flex items-center gap-2">
          <Gavel className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold tracking-tight">Court V2</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto font-sans">
          <SidebarItem 
            icon={LayoutDashboard} 
            label="Dashboard" 
            to="/" 
            active={location.pathname === '/'} 
          />
          <div className="pt-4 pb-2 px-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Evidence Modules</span>
          </div>
          <SidebarItem 
            icon={CalendarDays} 
            label="Events Timeline" 
            to="/events" 
            active={location.pathname.startsWith('/events')} 
          />
          <SidebarItem 
            icon={Mail} 
            label="Email Registry" 
            to="/emails/threads" 
            active={location.pathname.startsWith('/emails')} 
          />
          <SidebarItem 
            icon={FileText} 
            label="Documents" 
            to="/" 
            active={location.pathname.includes('/documents')} 
          />
          <div className="pt-4 pb-2 px-4">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Management</span>
          </div>
          <SidebarItem 
            icon={Briefcase} 
            label="Legal Cases" 
            to="/" 
            active={location.pathname.startsWith('/cases')} 
          />
        </nav>

        <div className="p-4 border-t bg-slate-50/50">
          <Button 
            variant="ghost" 
            className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 ml-64 flex flex-col">
        <Navbar />
        <main className="p-8 flex-1">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
