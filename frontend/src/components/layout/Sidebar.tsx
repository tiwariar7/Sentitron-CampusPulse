"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  ShieldAlert, Settings, LogOut, FileWarning, Bell,
  LayoutDashboard, Activity, Network, LineChart, TrendingUp
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Incident Feed', href: '/incidents', icon: Activity },
  { name: 'Semantic Clusters', href: '/clusters', icon: Network },
  { name: 'Analytics', href: '/analytics', icon: LineChart },
  { name: 'Forecasting', href: '/forecasting', icon: TrendingUp },
  { name: 'Monitoring', href: '/monitoring', icon: ShieldAlert },
  { name: 'Notifications', href: '/notifications', icon: Bell, alert: true },
  { name: 'Reports', href: '/reports', icon: FileWarning },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const allowedItems = NAV_ITEMS.filter((item) => {
    if (user.role === 'admin') return true;
    if (user.role === 'moderator') {
      return ['Dashboard', 'Incident Feed', 'Semantic Clusters', 'Analytics', 'Forecasting', 'Notifications', 'Reports'].includes(item.name);
    }
    if (user.role === 'user') {
      return ['Dashboard', 'Incident Feed', 'Notifications', 'Reports'].includes(item.name);
    }
    if (user.role === 'guest') {
      return ['Dashboard'].includes(item.name);
    }
    return false;
  });

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-950/80 backdrop-blur-xl border-r border-slate-800 flex flex-col z-40 pt-24 animate-fade-in">
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {allowedItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                isActive 
                  ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
                  : 'text-slate-400 hover:bg-slate-900/50 hover:text-slate-200'
              }`}
            >
              <item.icon className={`w-5 h-5 ${isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
              <span className="font-medium text-sm tracking-wide">{item.name}</span>
              {item.alert && (
                <div className="ml-auto w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)] animate-pulse" />
              )}
              {isActive && !item.alert && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_5px_rgba(99,102,241,0.8)] animate-pulse" />
              )}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-800">
        <button 
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 w-full text-left rounded-xl text-slate-400 hover:bg-slate-900/50 hover:text-rose-400 transition-all group duration-200"
        >
          <LogOut className="w-5 h-5 text-slate-500 group-hover:text-rose-400 transition-colors" />
          <span className="font-medium text-sm tracking-wide">Logout</span>
        </button>
      </div>
    </aside>
  );
}
