import { Search, Zap, Bell, User as UserIcon } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';

export function TopHeader() {
  const { user } = useAuth();

  const displayName = user ? user.username : "Guest User";
  const displayRole = user ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "Limited Access";

  return (
    <header className="fixed top-0 w-full z-50 h-24 flex justify-between items-center bg-slate-950/80 backdrop-blur-xl border-b border-slate-800 shadow-2xl pl-6 pr-6">
      <Link href="/dashboard" className="flex items-center gap-3 w-56">
        <div className="w-24 h-24 rounded-2xl overflow-hidden border border-slate-800 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.3)]">
          <img src="/logo.png" alt="CampusPulse Logo" className="w-full h-full object-contain" />
        </div>
      </Link>
      
      <div className="flex-1 max-w-2xl mx-8">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />
          <input 
            type="text" 
            placeholder="Search semantic clusters, incident IDs..." 
            className="w-full bg-slate-900/50 border border-slate-800 rounded-full py-1.5 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
          />
        </div>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-xs shadow-inner">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
          <span className="text-slate-300 font-medium tracking-wide">Live Inference</span>
        </div>
        
        <div className="flex items-center gap-4 border-l border-slate-800 pl-4">
          <button className="relative text-slate-400 hover:text-slate-200 transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full border-2 border-slate-950"></span>
          </button>
          
          <div className="flex items-center gap-2 cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
              <UserIcon className="w-4 h-4 text-slate-400" />
            </div>
            <div className="hidden md:block text-xs">
              <p className="text-slate-200 font-medium">{displayName}</p>
              <p className="text-slate-500">{displayRole}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
