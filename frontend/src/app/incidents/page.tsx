"use client";

import React, { useState, useEffect } from 'react';
import { Activity, Filter, Search, Smartphone, BookOpen, MoreVertical } from 'lucide-react';
import { formatTimeToIST } from '@/lib/utils';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

interface Event {
  complaint_id: string;
  timestamp: string;
  source: string;
  category: string;
  urgency_level: number;
  complaint_text: string;
  duplicate_group_id?: string;
}

function IncidentsFeed() {
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    const fetchIncidents = () => {
      apiFetch('/api/incidents')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setEvents(data);
          } else {
            console.error("Expected incidents array but got:", data);
          }
        })
        .catch(err => console.error(err));
    };

    fetchIncidents();
    const interval = setInterval(fetchIncidents, 3000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="p-8 max-w-[1600px] mx-auto min-h-screen">
      <div className="flex justify-between items-end mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Activity className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold tracking-tight">Real-Time Incident Feed</h1>
          </div>
          <p className="text-slate-400">Live operational event stream and ingestion monitor.</p>
        </div>
        
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input type="text" placeholder="Filter stream..." className="bg-slate-900/50 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-blue-500" />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm hover:bg-slate-800 transition-colors">
            <Filter className="w-4 h-4" /> Filters
          </button>
        </div>
      </div>

      {/* SOC Style Stream Table */}
      <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="grid grid-cols-12 gap-4 p-4 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-950/50">
          <div className="col-span-2">Timestamp / ID</div>
          <div className="col-span-1">Source</div>
          <div className="col-span-2">Category</div>
          <div className="col-span-4">Raw Content</div>
          <div className="col-span-2">AI Cluster</div>
          <div className="col-span-1 text-right">Actions</div>
        </div>
        
        <div className="divide-y divide-slate-800/50">
          {events.map((evt, i) => (
            <div key={evt.complaint_id} className="grid grid-cols-12 gap-4 p-4 items-center hover:bg-slate-800/30 transition-colors group cursor-pointer relative overflow-hidden">
              {i === 0 && <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)] animate-pulse" />}
              
              <div className="col-span-2 flex flex-col">
                <span className="text-slate-200 font-mono text-sm">{formatTimeToIST(evt.timestamp)}</span>
                <span className="text-slate-500 text-xs">{evt.complaint_id}</span>
              </div>
              
              <div className="col-span-1">
                <span className="flex items-center gap-1.5 text-xs text-slate-400">
                  {evt.source === 'WhatsApp' ? <Smartphone className="w-3 h-3 text-emerald-400" /> : <BookOpen className="w-3 h-3 text-purple-400" />}
                  {evt.source}
                </span>
              </div>
              
              <div className="col-span-2 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${evt.urgency_level >= 4 ? 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]' : evt.urgency_level === 3 ? 'bg-orange-500' : 'bg-slate-500'}`} />
                <span className="text-sm text-slate-300">{evt.category}</span>
              </div>
              
              <div className="col-span-4">
                <p className="text-sm text-slate-200 truncate pr-4">&ldquo;{evt.complaint_text}&rdquo;</p>
              </div>
              
              <div className="col-span-2">
                {evt.duplicate_group_id ? (
                  <span className="px-2.5 py-1 text-[10px] font-bold tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 rounded shadow-[0_0_10px_rgba(99,102,241,0.1)]">
                    {evt.duplicate_group_id}
                  </span>
                ) : (
                  <span className="text-xs text-slate-600">-</span>
                )}
              </div>
              
              <div className="col-span-1 flex justify-end">
                <button className="p-1.5 text-slate-500 hover:text-slate-200 rounded-md hover:bg-slate-700 transition-colors">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function IncidentsFeedWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator", "user"]}>
      <IncidentsFeed />
    </ProtectedRoute>
  );
}
