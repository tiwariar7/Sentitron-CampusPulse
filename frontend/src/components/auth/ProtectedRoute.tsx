"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { ShieldAlert } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#090b11] text-slate-100">
        <div className="relative flex flex-col items-center p-8 rounded-2xl border border-slate-800/80 bg-slate-900/50 backdrop-blur-xl">
          <div className="w-12 h-12 rounded-full border-4 border-indigo-500/30 border-t-indigo-500 animate-spin mb-4"></div>
          <p className="text-slate-400 font-medium">Validating session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center p-4">
        <div className="max-w-md w-full p-8 rounded-2xl border border-rose-500/20 bg-slate-900/40 backdrop-blur-xl text-center shadow-2xl">
          <div className="w-16 h-16 bg-rose-500/10 text-rose-500 rounded-full flex items-center justify-center mx-auto mb-6 border border-rose-500/20">
            <ShieldAlert size={32} className="animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Access Denied</h2>
          <p className="text-slate-400 mb-6">
            Your role (<span className="text-rose-400 font-semibold">{user.role}</span>) does not have permission to view this section.
          </p>
          <button
            onClick={() => router.push("/dashboard")}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg shadow-indigo-600/20"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
