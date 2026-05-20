"use client";

import React, { useState, useEffect } from 'react';
import { Server, Activity, Database, Zap, Cpu } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

const METRICS_DATA = [
  { time: '10:00', latency: 45, gpu: 30, qdrant: 12 },
  { time: '10:05', latency: 48, gpu: 35, qdrant: 15 },
  { time: '10:10', latency: 120, gpu: 85, qdrant: 45 }, // Spike
  { time: '10:15', latency: 85, gpu: 65, qdrant: 22 },
  { time: '10:20', latency: 42, gpu: 32, qdrant: 11 },
  { time: '10:25', latency: 44, gpu: 31, qdrant: 14 },
];

interface Metrics {
  gpu_utilization: number;
  inference_latency_ms: number;
  kafka_throughput_sec: number;
  qdrant_status: string;
}

function SystemMonitoring() {
  const [metrics, setMetrics] = useState<Metrics>({
    gpu_utilization: 32,
    inference_latency_ms: 45,
    kafka_throughput_sec: 1240,
    qdrant_status: "Healthy"
  });

  useEffect(() => {
    const interval = setInterval(() => {
      apiFetch('/api/monitoring/metrics')
        .then(res => res.json())
        .then(data => {
          if (data && typeof data === 'object' && 'gpu_utilization' in data) {
            setMetrics(data as Metrics);
          } else {
            console.error("Invalid metrics data received:", data);
          }
        })
        .catch(console.error);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-[1600px] mx-auto min-h-screen">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-8 h-8 text-emerald-500" />
          <h1 className="text-3xl font-bold tracking-tight">AI System Monitoring</h1>
        </div>
        <p className="text-slate-400">DevOps observability for AI inference pipelines and streaming architecture.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 rounded-lg">
            <Cpu className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <div className="text-2xl font-semibold text-slate-100">{metrics.gpu_utilization}%</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider">GPU Utilization</div>
          </div>
        </div>
        
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 rounded-lg">
            <Zap className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <div className="text-2xl font-semibold text-slate-100">{metrics.inference_latency_ms}ms</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider">Avg Inference Latency</div>
          </div>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 rounded-lg">
            <Server className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <div className="text-2xl font-semibold text-slate-100">{metrics.kafka_throughput_sec} /s</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider">Kafka Throughput</div>
          </div>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 rounded-lg">
            <Database className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <div className="text-2xl font-semibold text-slate-100">{metrics.qdrant_status}</div>
            <div className="text-xs text-slate-500 uppercase tracking-wider">Qdrant Vector DB</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6">AI Inference Latency (ms)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={METRICS_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
                <Line type="monotone" dataKey="latency" stroke="#10b981" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6">GPU Memory Usage (%)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={METRICS_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} />
                <Line type="monotone" dataKey="gpu" stroke="#3b82f6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SystemMonitoringWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin"]}>
      <SystemMonitoring />
    </ProtectedRoute>
  );
}
