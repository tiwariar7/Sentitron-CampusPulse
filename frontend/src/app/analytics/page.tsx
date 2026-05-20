"use client";

import React, { useState, useEffect } from 'react';
import { BarChart as BarIcon, LineChart as LineIcon, Activity, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];

interface DepartmentData {
  name: string;
  incidents: number;
}

interface SourceData {
  name: string;
  value: number;
}

interface AnalyticsData {
  departments: DepartmentData[];
  sources: SourceData[];
  critical_escalations: number;
}

function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData>({ departments: [], sources: [], critical_escalations: 0 });

  useEffect(() => {
    const fetchAnalytics = () => {
      apiFetch('/api/analytics/health')
        .then(res => res.json())
        .then(json => {
          if (json && typeof json === 'object' && 'departments' in json) {
            setData(json as AnalyticsData);
          } else {
            console.error("Invalid analytics data received:", json);
          }
        })
        .catch(err => console.error(err));
    };

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-[1600px] mx-auto min-h-screen">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <BarIcon className="w-8 h-8 text-indigo-500" />
          <h1 className="text-3xl font-bold tracking-tight">Campus Health Analytics</h1>
        </div>
        <p className="text-slate-400">Executive-level intelligence and operational KPIs.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <div className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-semibold">Overall Campus Health</div>
              <div className="text-3xl font-bold text-slate-100">82.4%</div>
            </div>
            <div className="p-3 bg-emerald-500/10 rounded-xl">
              <Activity className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
          <div className="text-sm text-emerald-400 font-medium">+2.1% from last month</div>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <div className="text-slate-400 text-sm mb-1 uppercase tracking-wider font-semibold">Avg Resolution Time</div>
              <div className="text-3xl font-bold text-slate-100">14.2 hrs</div>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-xl">
              <LineIcon className="w-6 h-6 text-blue-400" />
            </div>
          </div>
          <div className="text-sm text-blue-400 font-medium">-1.4 hrs from last month</div>
        </div>

        <div className="bg-slate-900/40 border border-rose-500/30 rounded-2xl p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-rose-500/5 pointer-events-none" />
          <div className="flex justify-between items-start mb-4 relative z-10">
            <div>
              <div className="text-rose-400 text-sm mb-1 uppercase tracking-wider font-semibold">Critical Escalations</div>
              <div className="text-3xl font-bold text-slate-100">{data.critical_escalations}</div>
            </div>
            <div className="p-3 bg-rose-500/10 rounded-xl">
              <AlertCircle className="w-6 h-6 text-rose-400" />
            </div>
          </div>
          <div className="text-sm text-rose-400 font-medium">Requires immediate attention</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6">Incidents by Department</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.departments}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{ fill: '#1e293b' }}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                />
                <Bar dataKey="incidents" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6">Ingestion Sources</h3>
          <div className="h-72 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.sources}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {data.sources.map((entry: SourceData, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="absolute flex flex-col gap-3 ml-48">
              {data.sources.map((entry: SourceData, i: number) => (
                <div key={entry.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-sm text-slate-300">{entry.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsDashboardWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator"]}>
      <AnalyticsDashboard />
    </ProtectedRoute>
  );
}
