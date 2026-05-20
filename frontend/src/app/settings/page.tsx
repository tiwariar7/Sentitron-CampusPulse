"use client";

import { useState, useEffect, useCallback } from 'react';
import { Settings as SettingsIcon, Save, ShieldAlert, History } from 'lucide-react';
import { formatToIST } from '@/lib/utils';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

interface AuditLog {
  id: number;
  timestamp: string;
  administrator_identity: string;
  action: string;
  modified_parameters: string;
  previous_values: string;
  updated_values: string;
}

interface Settings {
  critical_escalation_score?: number;
  toxicity_threshold?: number;
}

function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({});
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [role, setRole] = useState<string>('Super Admin');
  const [loading, setLoading] = useState(true);

  const fetchSettings = useCallback(async () => {
    try {
      const res = await apiFetch('/api/settings', {
        headers: { 'x-user-role': role }
      });
      const data = await res.json();
      if (res.ok && data) {
        setSettings(data.settings || {});
        setAuditLogs(data.audit_logs || []);
      }
    } catch (err) {
      console.error("Failed to fetch settings", err);
      setSettings({});
      setAuditLogs([]);
    } finally {
      setLoading(false);
    }
  }, [role]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchSettings();
  }, [fetchSettings]);

  const saveSettings = async () => {
    try {
      const res = await apiFetch('/api/settings', {
        method: 'POST',
        headers: {
          'x-user-role': role
        },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        // refresh to get new audit logs
        fetchSettings();
      }
    } catch (err) {
      console.error("Failed to save settings", err);
    }
  };

  if (loading) return <div className="p-8 text-slate-400">Loading Configuration...</div>;

  return (
    <div className="p-8 pb-24 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex justify-between items-end border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <SettingsIcon className="w-8 h-8 text-blue-400" />
            Operational Intelligence Configuration
          </h1>
          <p className="text-slate-400 mt-2">
            Manage AI governance controls, escalation thresholds, and platform settings.
          </p>
        </div>
        <div className="flex gap-4">
           <select 
             value={role} 
             onChange={(e) => setRole(e.target.value)}
             className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 outline-none"
           >
             <option value="Super Admin">Super Admin</option>
             <option value="Analytics Admin">Analytics Admin</option>
             <option value="Department Admin">Department Admin</option>
             <option value="Monitoring Viewer">Monitoring Viewer</option>
           </select>
           <button 
             onClick={saveSettings}
             disabled={role !== 'Super Admin' && role !== 'Analytics Admin'}
             className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg transition-colors font-medium text-sm shadow-[0_0_15px_rgba(37,99,235,0.4)]"
           >
             <Save className="w-4 h-4" /> Save Configuration
           </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
          <h2 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            AI Escalation Thresholds
          </h2>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Critical Escalation Score Limit
              </label>
              <input 
                type="number" 
                value={settings.critical_escalation_score || 85}
                onChange={(e) => setSettings({...settings, critical_escalation_score: parseInt(e.target.value)})}
                disabled={role !== 'Super Admin' && role !== 'Analytics Admin'}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
              />
              <p className="text-xs text-slate-500 mt-1">Triggers immediate CRITICAL alert.</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">
                Toxicity Threshold (%)
              </label>
              <input 
                type="number" 
                value={settings.toxicity_threshold || 70}
                onChange={(e) => setSettings({...settings, toxicity_threshold: parseInt(e.target.value)})}
                disabled={role !== 'Super Admin' && role !== 'Analytics Admin'}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors disabled:opacity-50"
              />
              <p className="text-xs text-slate-500 mt-1">Flag incidents with toxicity score above this value.</p>
            </div>
          </div>
        </section>

        <section className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm flex flex-col h-[500px]">
          <h2 className="text-xl font-bold text-slate-200 mb-6 flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Configuration Audit Log
          </h2>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2">
            {auditLogs.length === 0 ? (
              <p className="text-slate-500 text-sm">No recent configuration changes or permission denied.</p>
            ) : (
              auditLogs.map((log) => (
                <div key={log.id} className="p-4 bg-slate-950/50 rounded-xl border border-slate-800">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-slate-300">{log.action}</span>
                    <span className="text-xs text-slate-500">{formatToIST(log.timestamp)}</span>
                  </div>
                  <p className="text-xs text-slate-400 mb-1">By: {log.administrator_identity}</p>
                  <div className="text-xs text-slate-500 mt-2 bg-slate-900 p-2 rounded">
                    <p className="font-mono truncate">Modified: {log.modified_parameters}</p>
                    <p className="font-mono text-emerald-400 truncate">New: {log.updated_values}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default function SettingsPageWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator"]}>
      <SettingsPage />
    </ProtectedRoute>
  );
}

