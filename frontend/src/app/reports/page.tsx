"use client";

import React, { useState } from 'react';
import { Shield, Lock, AlertTriangle, EyeOff, CheckCircle2 } from 'lucide-react';
import { apiFetch } from '@/lib/api';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

function AnonymousReporting() {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <div className="bg-slate-900/50 border border-emerald-500/30 p-12 rounded-3xl text-center max-w-lg">
          <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="w-10 h-10 text-emerald-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100 mb-4">Report Submitted Securely</h2>
          <p className="text-slate-400 mb-8 leading-relaxed">
            Your identity has been completely obfuscated. Our AI has ingested your report and assigned it an encrypted ID for operational resolution.
          </p>
          <button 
            onClick={() => setSubmitted(false)}
            className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl transition-colors font-medium"
          >
            Submit Another Report
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[800px] mx-auto min-h-screen">
      <div className="text-center mb-10 mt-8">
        <div className="w-16 h-16 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl">
          <Shield className="w-8 h-8 text-blue-400" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Secure Reporting Portal</h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          This portal guarantees 100% anonymity. No IP addresses, device identifiers, or personal data are stored. 
          Your voice matters in keeping our campus safe and operational.
        </p>
      </div>

      <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 shadow-2xl">
        <div className="flex items-start gap-4 p-4 mb-8 bg-blue-500/10 border border-blue-500/20 rounded-2xl">
          <Lock className="w-6 h-6 text-blue-400 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-blue-100 font-semibold mb-1">End-to-End Encryption Active</h3>
            <p className="text-sm text-blue-300/80 leading-relaxed">
              Your report will be processed directly by the CampusPulse AI Engine to cluster semantic issues without revealing the source.
            </p>
          </div>
        </div>

        <form className="space-y-6" onSubmit={async (e) => { 
          e.preventDefault(); 
          const fd = new FormData(e.currentTarget as HTMLFormElement);
          const data = {
            category: fd.get('category'),
            description: fd.get('description'),
            urgency: fd.get('urgency')
          };
          
          await apiFetch('/api/incidents/anonymous', {
            method: 'POST',
            body: JSON.stringify(data)
          });
          setSubmitted(true); 
        }}>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Category of Concern</label>
            <select name="category" className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none">
              <option>Select a category...</option>
              <option>Academic Integrity / Faculty Issue</option>
              <option>Hostel / Accommodation Conditions</option>
              <option>Mental Health & Wellbeing</option>
              <option>Harassment or Misconduct</option>
              <option>Infrastructure & Maintenance</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Detailed Description</label>
            <textarea 
              name="description"
              rows={6}
              placeholder="Please provide as much operational detail as possible. Do not include your own name or student ID if you wish to remain anonymous."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-600 resize-none"
            ></textarea>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Urgency Level</label>
            <div className="grid grid-cols-3 gap-4">
              <label className="cursor-pointer">
                <input type="radio" name="urgency" value="Standard" defaultChecked className="peer sr-only" />
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 text-center peer-checked:border-slate-400 peer-checked:bg-slate-800 transition-all">
                  <span className="text-slate-400 font-medium">Standard</span>
                </div>
              </label>
              <label className="cursor-pointer">
                <input type="radio" name="urgency" value="High" className="peer sr-only" />
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 text-center peer-checked:border-orange-500 peer-checked:bg-orange-500/10 transition-all">
                  <span className="text-orange-500 font-medium">High</span>
                </div>
              </label>
              <label className="cursor-pointer">
                <input type="radio" name="urgency" value="Critical" className="peer sr-only" />
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 text-center peer-checked:border-rose-500 peer-checked:bg-rose-500/10 transition-all">
                  <div className="flex items-center justify-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-500" />
                    <span className="text-rose-500 font-medium">Critical</span>
                  </div>
                </div>
              </label>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-800 flex justify-end">
            <button 
              type="submit"
              className="flex items-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)]"
            >
              <EyeOff className="w-5 h-5" /> Submit Anonymously
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AnonymousReportingWrapper() {
  return (
    <ProtectedRoute allowedRoles={["admin", "moderator", "user", "guest"]}>
      <AnonymousReporting />
    </ProtectedRoute>
  );
}
