import React from 'react';
import Navbar from './Navbar';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-slate-50">
    <Navbar />
    <main className="max-w-screen-xl mx-auto px-6 py-8">
      {children}
    </main>
  </div>
);

export default Layout;
