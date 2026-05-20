'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert, Send, CheckCircle2, AlertTriangle,
  ChevronDown, Lock, MessageSquare, Building2, Zap, Mail,
} from 'lucide-react';

const DEPARTMENTS = [
  'CSE', 'ECE', 'ME', 'Civil', 'Hostel', 'Transport',
  'Security', 'Academics', 'Administration', 'Student Welfare', 'Other',
];

const CATEGORIES = [
  'Infrastructure', 'Safety & Security', 'Academic Integrity',
  'Harassment', 'Hostel / Accommodation', 'Food & Canteen',
  'Transport', 'IT / Network', 'Faculty Conduct', 'Other',
];

const SEVERITY_OPTIONS = [
  { value: 'Standard', label: 'Standard', color: '#6366f1', desc: 'Non-urgent — can wait 48h' },
  { value: 'High',     label: 'High',     color: '#f59e0b', desc: 'Needs resolution within 24h' },
  { value: 'Critical', label: 'Critical', color: '#ef4444', desc: 'Immediate action required' },
];

interface FormState {
  title: string;
  description: string;
  category: string;
  department: string;
  severity: string;
  contact_email: string;
}

const initialForm: FormState = {
  title: '',
  description: '',
  category: '',
  department: '',
  severity: 'Standard',
  contact_email: '',
};

export default function ReportPage() {
  const [form, setForm]         = useState<FormState>(initialForm);
  const [errors, setErrors]     = useState<Partial<FormState>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult]     = useState<{ id: string; correlation_id: string } | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const validate = (): boolean => {
    const e: Partial<FormState> = {};
    if (!form.title.trim() || form.title.length < 5)
      e.title = 'Title must be at least 5 characters';
    if (!form.description.trim() || form.description.length < 20)
      e.description = 'Description must be at least 20 characters';
    if (!form.category)
      e.category = 'Please select a category';
    if (!form.department)
      e.department = 'Please select a department';
    if (form.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email))
      e.contact_email = 'Enter a valid email address';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setApiError(null);

    try {
      const res = await fetch('/api/incidents/anonymous', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category:    form.category,
          description: `[${form.title}] ${form.description}`,
          urgency:     form.severity,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setResult({ id: data.id, correlation_id: data.correlation_id });
      setForm(initialForm);
    } catch (err: any) {
      setApiError(err.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const Field = ({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) => (
    <div style={{ marginBottom: 20 }}>
      <label style={{ display: 'block', color: '#94a3b8', fontSize: 12, textTransform: 'uppercase',
                      letterSpacing: '0.05em', marginBottom: 6, fontWeight: 600 }}>
        {label}
      </label>
      {children}
      {error && (
        <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
          style={{ color: '#f87171', fontSize: 12, marginTop: 4 }}>
          {error}
        </motion.p>
      )}
    </div>
  );

  const inputStyle: React.CSSProperties = {
    width: '100%', background: '#0f0f1f', border: '1px solid #2a2a4a',
    borderRadius: 8, padding: '10px 14px', color: '#f1f5f9', fontSize: 14,
    outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
  };

  if (result) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0a14', display: 'flex',
                    alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
          style={{ maxWidth: 480, width: '100%', background: 'linear-gradient(135deg,#0d1117,#0f0f1f)',
                   border: '1px solid #1e3a2f', borderRadius: 16, padding: 40, textAlign: 'center' }}>
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.2, type: 'spring' }}>
            <CheckCircle2 size={64} color="#22c55e" style={{ margin: '0 auto 20px' }} />
          </motion.div>
          <h2 style={{ color: '#f1f5f9', fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
            Report Submitted
          </h2>
          <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
            Your anonymous report has been received and is being processed by our AI pipeline.
          </p>
          <div style={{ background: '#0a1a12', border: '1px solid #1e3a2f', borderRadius: 10,
                        padding: 16, marginBottom: 24, textAlign: 'left' }}>
            <p style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', marginBottom: 4 }}>
              Complaint ID
            </p>
            <p style={{ color: '#22c55e', fontFamily: 'monospace', fontSize: 18, fontWeight: 700 }}>
              {result.id}
            </p>
            <p style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', marginBottom: 4, marginTop: 12 }}>
              Correlation ID
            </p>
            <p style={{ color: '#4ade80', fontFamily: 'monospace', fontSize: 12, wordBreak: 'break-all' }}>
              {result.correlation_id}
            </p>
          </div>
          <p style={{ color: '#475569', fontSize: 12 }}>
            Save your Complaint ID to track resolution status.
          </p>
          <button onClick={() => setResult(null)}
            style={{ marginTop: 20, padding: '10px 28px', background: '#4f46e5', color: '#fff',
                     border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
            Submit Another Report
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg,#0a0a14 0%,#0f0f1f 100%)',
                  display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
                  padding: '40px 24px', fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>
      <div style={{ maxWidth: 640, width: '100%' }}>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, background: '#1a1a2e',
                        border: '1px solid #2a2a4a', borderRadius: 9999, padding: '8px 20px',
                        marginBottom: 16 }}>
            <Lock size={14} color="#818cf8" />
            <span style={{ color: '#818cf8', fontSize: 13, fontWeight: 600 }}>
              Anonymous & Secure — No identity stored
            </span>
          </div>
          <h1 style={{ color: '#f1f5f9', fontSize: 28, fontWeight: 800, margin: '0 0 8px', letterSpacing: '-0.5px' }}>
            Submit a Campus Report
          </h1>
          <p style={{ color: '#64748b', fontSize: 15, maxWidth: 480, margin: '0 auto' }}>
            Your report will be processed by our AI pipeline — classified, clustered,
            and escalated to the appropriate authorities automatically.
          </p>
        </motion.div>

        {/* Form Card */}
        <motion.form initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }} onSubmit={handleSubmit}
          style={{ background: 'rgba(26,26,46,0.8)', backdropFilter: 'blur(12px)',
                   border: '1px solid #2a2a4a', borderRadius: 16, padding: 32 }}>

          {/* AI Pipeline indicator */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 28 }}>
            {['Classify','Cluster','Escalate','Notify'].map((step, i) => (
              <div key={step} style={{ display: 'flex', alignItems: 'center', gap: 6,
                                       background: '#0f0f1f', border: '1px solid #2a2a4a',
                                       borderRadius: 9999, padding: '4px 12px', fontSize: 12 }}>
                <Zap size={11} color="#6366f1" />
                <span style={{ color: '#94a3b8' }}>AI {step}</span>
              </div>
            ))}
          </div>

          {/* Title */}
          <Field label="Report Title *" error={errors.title}>
            <div style={{ position: 'relative' }}>
              <MessageSquare size={15} color="#475569"
                style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
              <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                placeholder="Brief title describing the issue"
                style={{ ...inputStyle, paddingLeft: 36, borderColor: errors.title ? '#ef4444' : '#2a2a4a' }} />
            </div>
          </Field>

          {/* Category + Department */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Field label="Category *" error={errors.category}>
              <div style={{ position: 'relative' }}>
                <select value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
                  style={{ ...inputStyle, appearance: 'none', paddingRight: 32,
                           borderColor: errors.category ? '#ef4444' : '#2a2a4a' }}>
                  <option value="">Select category</option>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <ChevronDown size={14} color="#475569"
                  style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              </div>
            </Field>
            <Field label="Department *" error={errors.department}>
              <div style={{ position: 'relative' }}>
                <Building2 size={15} color="#475569"
                  style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', zIndex: 1 }} />
                <select value={form.department} onChange={e => setForm(f => ({ ...f, department: e.target.value }))}
                  style={{ ...inputStyle, appearance: 'none', paddingLeft: 30, paddingRight: 32,
                           borderColor: errors.department ? '#ef4444' : '#2a2a4a' }}>
                  <option value="">Select dept</option>
                  {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
                <ChevronDown size={14} color="#475569"
                  style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              </div>
            </Field>
          </div>

          {/* Description */}
          <Field label="Description *" error={errors.description}>
            <textarea value={form.description} rows={5}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Provide a detailed description of the incident. Include time, location, and any relevant context."
              style={{ ...inputStyle, resize: 'vertical', borderColor: errors.description ? '#ef4444' : '#2a2a4a' }} />
          </Field>

          {/* Severity */}
          <Field label="Severity *">
            <div style={{ display: 'flex', gap: 10 }}>
              {SEVERITY_OPTIONS.map(opt => (
                <label key={opt.value} style={{ flex: 1, cursor: 'pointer' }}>
                  <input type="radio" name="severity" value={opt.value} checked={form.severity === opt.value}
                    onChange={() => setForm(f => ({ ...f, severity: opt.value }))} style={{ display: 'none' }} />
                  <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    style={{ padding: '10px 8px', borderRadius: 8, textAlign: 'center',
                             border: `2px solid ${form.severity === opt.value ? opt.color : '#2a2a4a'}`,
                             background: form.severity === opt.value ? `${opt.color}15` : '#0f0f1f',
                             transition: 'all 0.2s' }}>
                    <p style={{ color: form.severity === opt.value ? opt.color : '#64748b',
                                fontSize: 13, fontWeight: 700, margin: '0 0 2px' }}>{opt.label}</p>
                    <p style={{ color: '#475569', fontSize: 10, margin: 0 }}>{opt.desc}</p>
                  </motion.div>
                </label>
              ))}
            </div>
          </Field>

          {/* Optional email */}
          <Field label="Contact Email (optional)" error={errors.contact_email}>
            <div style={{ position: 'relative' }}>
              <Mail size={15} color="#475569"
                style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
              <input type="email" value={form.contact_email}
                onChange={e => setForm(f => ({ ...f, contact_email: e.target.value }))}
                placeholder="Only used for follow-up if you consent"
                style={{ ...inputStyle, paddingLeft: 36, borderColor: errors.contact_email ? '#ef4444' : '#2a2a4a' }} />
            </div>
            <p style={{ color: '#475569', fontSize: 11, marginTop: 4 }}>
              Your email is NOT stored in the report. It is only used for direct follow-up if you choose.
            </p>
          </Field>

          {/* API Error */}
          <AnimatePresence>
            {apiError && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                style={{ display: 'flex', gap: 8, alignItems: 'center', background: '#1c0a0a',
                         border: '1px solid #7f1d1d', borderRadius: 8, padding: '10px 14px', marginBottom: 16 }}>
                <AlertTriangle size={16} color="#f87171" />
                <span style={{ color: '#f87171', fontSize: 13 }}>{apiError}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Submit */}
          <motion.button type="submit" disabled={submitting}
            whileHover={{ scale: submitting ? 1 : 1.01 }} whileTap={{ scale: submitting ? 1 : 0.99 }}
            style={{ width: '100%', padding: '13px 24px', fontSize: 15, fontWeight: 700,
                     background: submitting ? '#2a2a4a' : 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                     color: submitting ? '#64748b' : '#fff', border: 'none', borderRadius: 10,
                     cursor: submitting ? 'not-allowed' : 'pointer', display: 'flex',
                     alignItems: 'center', justifyContent: 'center', gap: 8, transition: 'all 0.2s' }}>
            {submitting ? (
              <>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  style={{ width: 16, height: 16, border: '2px solid #475569',
                           borderTopColor: '#818cf8', borderRadius: '50%' }} />
                Processing via AI Pipeline...
              </>
            ) : (
              <>
                <ShieldAlert size={18} />
                Submit Anonymous Report
              </>
            )}
          </motion.button>

          <p style={{ color: '#1e3a5f', fontSize: 11, textAlign: 'center', marginTop: 12 }}>
            🔒 End-to-end anonymous. Your IP address is not logged by this portal.
          </p>
        </motion.form>

        {/* Pipeline steps diagram */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          style={{ marginTop: 24, background: 'rgba(15,15,31,0.6)', border: '1px solid #1e1e3a',
                   borderRadius: 12, padding: '16px 20px' }}>
          <p style={{ color: '#475569', fontSize: 11, textTransform: 'uppercase',
                      letterSpacing: '0.08em', marginBottom: 12 }}>
            What happens after you submit
          </p>
          <div style={{ display: 'flex', gap: 0, alignItems: 'center', overflowX: 'auto' }}>
            {[
              { icon: '📝', label: 'Validated' },
              { icon: '🤖', label: 'AI Classify' },
              { icon: '🧩', label: 'Clustered' },
              { icon: '⚡', label: 'Escalated' },
              { icon: '📧', label: 'Email Alert' },
              { icon: '🔔', label: 'Notified' },
              { icon: '📊', label: 'Tracked' },
            ].map((step, i) => (
              <div key={step.label} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ textAlign: 'center', padding: '4px 10px' }}>
                  <div style={{ fontSize: 18 }}>{step.icon}</div>
                  <div style={{ color: '#64748b', fontSize: 10, marginTop: 2 }}>{step.label}</div>
                </div>
                {i < 6 && <div style={{ color: '#1e1e3a', fontSize: 16, margin: '0 2px' }}>→</div>}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
