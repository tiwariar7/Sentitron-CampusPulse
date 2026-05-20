"use client";

import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, CalendarClock } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Line, Bar } from 'recharts';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const FORECAST_DATA = [
  { day: 'Mon', historical: 120, predicted: 125 },
  { day: 'Tue', historical: 145, predicted: 150 },
  { day: 'Wed', historical: 130, predicted: 140 },
  { day: 'Thu', historical: 180, predicted: 175 },
  { day: 'Fri', historical: null, predicted: 210 },
  { day: 'Sat', historical: null, predicted: 90 },
  { day: 'Sun', historical: null, predicted: 60 },
];

interface Forecast {
  surge_risk_probability: number;
  confidence: number;
  predicted_cluster: string;
}

function Forecasting() {
  const [forecast, setForecast] = useState<Forecast>({
    surge_risk_probability: 65,
    confidence: 94,
    predicted_cluster: "Hostel Maintenance"
  });

  useEffect(() => {
    const fetchForecast = () => {
      apiFetch('/api/forecasting/trends')
        .then(res => res.json())
        .then(data => {
          if (data) {
            setForecast({
              surge_risk_probability: data.surge_risk ?? 65,
              confidence: data.confidence ?? 94,
              predicted_cluster: data.predicted_cluster ?? "Hostel Maintenance"
            });
          }
        })
        .catch(console.error);
    };

    fetchForecast();
    const interval = setInterval(fetchForecast, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-[1600px] mx-auto min-h-screen">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <TrendingUp className="w-8 h-8 text-cyan-500" />
          <h1 className="text-3xl font-bold tracking-tight">Forecasting & Temporal Intelligence</h1>
        </div>
        <p className="text-slate-400">Predictive escalation analysis and recurring anomaly detection.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold tracking-tight">Volume Prediction (Next 72 Hrs)</h3>
            <span className="px-3 py-1 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded text-xs font-semibold">{forecast.confidence}% Confidence</span>
          </div>
          
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={FORECAST_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="day" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                <Bar dataKey="historical" fill="#3b82f6" fillOpacity={0.6} radius={[4, 4, 0, 0]} name="Actual Volume" />
                <Line type="monotone" dataKey="predicted" stroke="#06b6d4" strokeWidth={3} strokeDasharray="5 5" dot={false} name="AI Prediction" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900/40 border border-rose-500/30 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-rose-500/10 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              </div>
              <h3 className="text-lg font-semibold tracking-tight text-rose-100">Surge Risk Detected</h3>
            </div>
            <p className="text-slate-400 text-sm mb-4">
              AI predicts a {forecast.surge_risk_probability}% probability of a critical cluster emergence regarding &ldquo;{forecast.predicted_cluster}&rdquo; on Friday evening.
            </p>
            <div className="w-full bg-slate-950 rounded-full h-2 mb-2">
              <div className="bg-rose-500 h-2 rounded-full transition-all duration-1000" style={{ width: `${forecast.surge_risk_probability}%` }}></div>
            </div>
          </div>

          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-500/10 rounded-lg">
                <CalendarClock className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold tracking-tight text-indigo-100">Temporal Anomalies</h3>
            </div>
            <ul className="space-y-3">
              <li className="text-sm text-slate-300 pb-3 border-b border-slate-800/50">
                Unusual volume of Academic complaints (150% above baseline) detected today.
              </li>
              <li className="text-sm text-slate-300">
                Transport complaints typically spike at 9:00 AM on Mondays.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ForecastingWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator"]}>
      <Forecasting />
    </ProtectedRoute>
  );
}
