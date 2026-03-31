import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Search, Bell, User as UserIcon, Settings } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Link } from 'react-router-dom';

const Navbar: React.FC = () => {
  const { user } = useAuth();

  return (
    <header className="h-16 border-b bg-white flex items-center justify-between px-8 sticky top-0 z-40">
      <div className="flex items-center flex-1 max-w-xl">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search evidence, cases, or documents..." 
            className="pl-10 bg-slate-50 border-none focus-visible:ring-1 focus-visible:ring-primary w-full h-10"
          />
        </div>
      </div>

      <nav className="flex gap-4 ml-8">
        <Link to="/timeline" className="text-sm font-bold text-primary hover:underline">Timeline</Link>
        <Link to="/gallery" className="text-sm font-bold text-primary hover:underline">Evidence Gallery</Link>
      </nav>

      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="text-slate-500">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" className="text-slate-500">
          <Settings className="h-5 w-5" />
        </Button>
        <div className="h-8 w-px bg-slate-200 mx-2" />
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium leading-none">{user?.email?.split('@')[0]}</p>
            <p className="text-xs text-slate-500 mt-1 uppercase tracking-tighter font-bold">Admin</p>
          </div>
          <div className="h-9 w-9 rounded-full bg-slate-100 flex items-center justify-center border border-slate-200">
            <UserIcon className="h-5 w-5 text-slate-600" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
