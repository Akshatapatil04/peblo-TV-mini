import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Tv, Sliders, ShieldCheck, UserCheck, Sparkles } from 'lucide-react';
import { getActiveRole, setActiveRole } from '../api/client';
import { Role } from '../types';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [role, setRole] = useState<Role>(getActiveRole());
  const isCms = location.pathname.startsWith('/cms');

  useEffect(() => {
    const handleRoleChange = (e: any) => {
      setRole(e.detail);
    };
    window.addEventListener('peblo-role-change', handleRoleChange);
    return () => window.removeEventListener('peblo-role-change', handleRoleChange);
  }, []);

  const toggleRole = (newRole: Role) => {
    setActiveRole(newRole);
    setRole(newRole);
  };

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-opacity-90 border-b transition-colors"
      style={{
        backgroundColor: isCms ? 'rgba(11, 15, 25, 0.95)' : 'rgba(15, 16, 21, 0.9)',
        borderColor: isCms ? 'var(--border-cms)' : 'var(--border-viewer)'
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Surface Switcher */}
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2 group text-decoration-none">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-red-500 flex items-center justify-center shadow-lg shadow-red-500/30 group-hover:scale-105 transition-transform">
              <Tv className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-white font-display">PEBLO<span className="text-red-500">TV</span></span>
              <span className="text-[10px] tracking-widest uppercase font-semibold text-slate-400 block -mt-1">Mini Platform</span>
            </div>
          </Link>

          {/* Mode Switcher Pills */}
          <nav className="hidden md:flex items-center gap-1 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
            <Link
              to="/"
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                !isCms
                  ? 'bg-red-600 text-white shadow-md shadow-red-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              Viewer Mode
            </Link>
            <Link
              to="/cms"
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
                isCms
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sliders className="w-4 h-4" />
              CMS Console
            </Link>
          </nav>
        </div>

        {/* CMS Secondary Navigation (When in CMS) */}
        {isCms && (
          <div className="hidden lg:flex items-center gap-6 text-sm font-medium">
            <Link
              to="/cms"
              className={`transition-colors ${
                location.pathname === '/cms' ? 'text-blue-400 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Shows & Episodes
            </Link>
            <Link
              to="/cms/publish"
              className={`transition-colors flex items-center gap-1.5 ${
                location.pathname === '/cms/publish' ? 'text-blue-400 font-semibold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Validation & Publish
            </Link>
          </div>
        )}

        {/* Role Switcher Toolbar */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 p-1 bg-slate-900/90 rounded-lg border border-slate-800">
            <button
              type="button"
              onClick={() => toggleRole('admin')}
              className={`px-3 py-1 text-xs font-semibold rounded-md flex items-center gap-1.5 transition-all ${
                role === 'admin'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Admin Role: Full CRUD and Publish authority"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Admin
            </button>
            <button
              type="button"
              onClick={() => toggleRole('editor')}
              className={`px-3 py-1 text-xs font-semibold rounded-md flex items-center gap-1.5 transition-all ${
                role === 'editor'
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Editor Role: Content CRUD only. Blocked from publishing."
            >
              <UserCheck className="w-3.5 h-3.5" />
              Editor
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
