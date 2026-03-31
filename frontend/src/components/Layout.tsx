import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogOut, Gavel, LayoutDashboard, ChevronRight, Image } from 'lucide-react';
import { Button } from './ui/button';

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
  const { logout, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="w-64 bg-white border-r flex flex-col fixed inset-y-0 shadow-sm z-50">
        <div className="p-6 border-b flex items-center gap-2">
          <Gavel className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold tracking-tight text-slate-900">Court V2</span>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <SidebarItem
            icon={LayoutDashboard}
            label="Home"
            to="/"
            active={location.pathname === '/'}
          />
          <SidebarItem
            icon={Image}
            label="Photo Documents"
            to="/photos/documents"
            active={location.pathname.startsWith('/photos')}
          />
        </nav>

        <div className="p-4 border-t">
          <div className="text-xs text-slate-500 mb-3 px-1 truncate">{user?.email}</div>
          <Button
            variant="ghost"
            className="w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50 font-medium text-sm"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Log Out
          </Button>
        </div>
      </aside>

      <div className="flex-1 ml-64">
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;