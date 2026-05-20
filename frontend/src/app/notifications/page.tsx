"use client";

import { useState, useEffect, useRef, useCallback } from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle, XCircle, Info, Activity, Zap } from 'lucide-react';
import { formatToIST } from '@/lib/utils';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

interface Notification {
  id: number;
  title: string;
  message: string;
  severity: 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
  category: string;
  lifecycle_state: 'CREATED' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';
  timestamp: string;
  ai_recommendations?: {
    action: string;
    similar_incident?: string;
  };
  related_entity_id?: string;
}

function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const ws = useRef<WebSocket | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await apiFetch('/api/notifications');
      const data = await res.json();
      if (Array.isArray(data)) {
        setNotifications(data);
      } else {
        console.error("Expected notifications array but got:", data);
        setNotifications([]);
      }
    } catch (err) {
      console.error(err);
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchNotifications();

    // WebSocket connection
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const wsUrl = `ws://localhost:8000/ws/notifications${token ? `?token=${token}` : ''}`;
    ws.current = new WebSocket(wsUrl);
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'NEW_NOTIFICATION') {
        setNotifications(prev => [data.notification, ...prev]);
      }
    };

    return () => {
      ws.current?.close();
    };
  }, [fetchNotifications]);

  const handleAction = async (id: number, action: string) => {
    try {
      await apiFetch(`/api/notifications/${id}/${action}`, { method: 'POST' });
      // Update local state
      setNotifications(prev => prev.map(n => 
        n.id === id ? { ...n, lifecycle_state: (action.toUpperCase() + 'D') as Notification['lifecycle_state'] } : n
      ));
    } catch (err) {
      console.error(err);
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'UNRESOLVED') return n.lifecycle_state === 'CREATED' || n.lifecycle_state === 'ACKNOWLEDGED';
    if (filter === 'CRITICAL') return n.severity === 'CRITICAL';
    return true;
  });

  // Sort to pin CRITICAL unresolved to top
  const sortedNotifications = [...filteredNotifications].sort((a, b) => {
    const aPin = (a.severity === 'CRITICAL' && (a.lifecycle_state === 'CREATED' || a.lifecycle_state === 'ACKNOWLEDGED')) ? 1 : 0;
    const bPin = (b.severity === 'CRITICAL' && (b.lifecycle_state === 'CREATED' || b.lifecycle_state === 'ACKNOWLEDGED')) ? 1 : 0;
    return bPin - aPin; // pinned first
  });

  const getSeverityGlow = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-rose-500/10 border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.3)]';
      case 'HIGH': return 'bg-orange-500/10 border-orange-500/50';
      case 'WARNING': return 'bg-amber-500/10 border-amber-500/50';
      default: return 'bg-blue-500/10 border-blue-500/50';
    }
  };
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <ShieldAlert className="w-5 h-5 text-rose-500 animate-pulse" />;
      case 'HIGH': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'WARNING': return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  if (loading) return <div className="p-8 text-slate-400">Loading Command Center...</div>;

  return (
    <div className="p-8 pb-24 space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-5xl mx-auto">
      <header className="flex justify-between items-end border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Activity className="w-8 h-8 text-rose-400" />
            Notification Intelligence Center
          </h1>
          <p className="text-slate-400 mt-2">
            Real-time operational alerts, anomaly detections, and AI-driven command responses.
          </p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setFilter('ALL')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === 'ALL' ? 'bg-slate-700 text-white' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}
          >
            All Alerts
          </button>
          <button 
            onClick={() => setFilter('UNRESOLVED')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === 'UNRESOLVED' ? 'bg-slate-700 text-white' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'}`}
          >
            Unresolved
          </button>
          <button 
            onClick={() => setFilter('CRITICAL')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === 'CRITICAL' ? 'bg-rose-900/50 text-rose-200 border border-rose-500/30' : 'bg-slate-900 text-rose-400/70 hover:bg-slate-800'}`}
          >
            Critical Only
          </button>
        </div>
      </header>

      <div className="space-y-4">
        {sortedNotifications.length === 0 && (
          <div className="text-center py-20 text-slate-500 bg-slate-900/50 rounded-2xl border border-slate-800">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-emerald-500/50" />
            <p className="text-lg font-medium">All clear.</p>
            <p className="text-sm">No operational alerts to display.</p>
          </div>
        )}
        
        {sortedNotifications.map((notif, idx) => (
          <div 
            key={notif.id} 
            className={`p-5 rounded-2xl border transition-all duration-300 flex flex-col md:flex-row gap-6 items-start animate-in fade-in slide-in-from-top-4 ${getSeverityGlow(notif.severity)} ${notif.lifecycle_state === 'RESOLVED' || notif.lifecycle_state === 'DISMISSED' ? 'opacity-60 grayscale-[50%]' : ''}`}
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <div className="flex-shrink-0 mt-1">
              {getSeverityIcon(notif.severity)}
            </div>
            
            <div className="flex-1 space-y-3">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-lg font-bold text-slate-200">{notif.title}</h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                    {notif.category}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${notif.lifecycle_state === 'CREATED' ? 'bg-blue-500/20 text-blue-300' : notif.lifecycle_state === 'ACKNOWLEDGED' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-800 text-slate-500'}`}>
                    {notif.lifecycle_state}
                  </span>
                </div>
                <p className="text-slate-300">{notif.message}</p>
                <p className="text-xs text-slate-500 mt-2 font-mono">
                  {formatToIST(notif.timestamp)} {notif.related_entity_id && `• Entity ID: ${notif.related_entity_id}`}
                </p>
              </div>

              {notif.ai_recommendations && (
                <div className="bg-slate-950/80 rounded-xl p-4 border border-indigo-500/30 mt-3 shadow-inner">
                  <div className="flex items-center gap-2 mb-2 text-indigo-400">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm font-semibold tracking-wide">AI Recommendation</span>
                  </div>
                  <p className="text-sm text-slate-300 mb-2">
                    {notif.ai_recommendations.action}
                  </p>
                  {notif.ai_recommendations.similar_incident && (
                    <p className="text-xs text-indigo-300/70 bg-indigo-950/50 p-2 rounded">
                      Historical Context: Similar pattern detected in &apos;{notif.ai_recommendations.similar_incident}&apos;
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-row md:flex-col gap-2 flex-shrink-0 w-full md:w-auto">
              {(notif.lifecycle_state === 'CREATED' || notif.lifecycle_state === 'ACKNOWLEDGED') && (
                <>
                  {notif.lifecycle_state === 'CREATED' && (
                    <button 
                      onClick={() => handleAction(notif.id, 'acknowledge')}
                      className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium transition-colors border border-amber-500/20"
                    >
                      <Info className="w-4 h-4" /> Acknowledge
                    </button>
                  )}
                  <button 
                    onClick={() => handleAction(notif.id, 'resolve')}
                    className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-sm font-medium transition-colors border border-emerald-500/20"
                  >
                    <CheckCircle className="w-4 h-4" /> Resolve
                  </button>
                  <button 
                    onClick={() => handleAction(notif.id, 'dismiss')}
                    className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg text-sm font-medium transition-colors border border-slate-700"
                  >
                    <XCircle className="w-4 h-4" /> Dismiss
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function NotificationsPageWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator", "user"]}>
      <NotificationsPage />
    </ProtectedRoute>
  );
}
