"use client";

import { usePathname } from "next/navigation";
import { AuthProvider } from "@/context/AuthContext";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopHeader } from "@/components/layout/TopHeader";

export default function LayoutContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === "/auth" || pathname?.startsWith("/auth/");

  if (isAuthPage) {
    return (
      <AuthProvider>
        <main className="flex-1 min-h-screen bg-[#090b11] text-slate-100 overflow-y-auto">
          {children}
        </main>
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <TopHeader />
      <div className="flex h-screen pt-24 overflow-hidden">
        <Sidebar />
        <main className="flex-1 ml-64 overflow-y-auto bg-[#090b11] text-slate-100">
          {children}
        </main>
      </div>
    </AuthProvider>
  );
}
