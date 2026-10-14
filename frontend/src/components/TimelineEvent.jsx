import React from 'react';
import {
  AlertCircle, Calendar, Pill, Activity, Stethoscope, Building2, Syringe,
  HeartPulse, FlaskConical, Gauge, ShieldCheck, ShieldAlert, Users,
} from 'lucide-react';

const CONFIG = {
  Diagnosis:  { badge: 'bg-purple-100 text-purple-700', icon: Activity },
  Medication: { badge: 'bg-green-100 text-green-700',   icon: Pill },
  'Lab Result': { badge: 'bg-amber-100 text-amber-700', icon: FlaskConical },
  'Vital Sign': { badge: 'bg-teal-100 text-teal-700',   icon: Gauge },
  Visit:      { badge: 'bg-blue-100 text-blue-700',     icon: Building2 },
  Procedure:  { badge: 'bg-cyan-100 text-cyan-700',     icon: Syringe },
  Symptom:    { badge: 'bg-rose-100 text-rose-700',     icon: HeartPulse },
  'Family History': { badge: 'bg-indigo-100 text-indigo-700', icon: Users },
  Other:      { badge: 'bg-slate-100 text-slate-700',   icon: Stethoscope },
};

const ACTION_STYLE = {
  started: 'bg-green-50 text-green-700 border-green-200',
  increased: 'bg-orange-50 text-orange-700 border-orange-200',
  decreased: 'bg-sky-50 text-sky-700 border-sky-200',
  stopped: 'bg-red-50 text-red-700 border-red-200',
};


// "98%" + unit "%" must not render as "98% %"
const labDisplay = (lab) => {
  const v = lab.value_text ?? lab.value;
  const u = lab.unit || '';
  if (!u || String(v).toLowerCase().includes(u.toLowerCase())) return String(v);
  return `${v} ${u}`;
};

const refDisplay = (lab) => {
  const { reference_low: lo, reference_high: hi, unit } = lab;
  const u = unit ? ` ${unit}` : '';
  if (lo != null && hi != null) return `${lo} – ${hi}${u}`;
  if (hi != null) return `< ${hi}${u}`;
  if (lo != null) return `> ${lo}${u}`;
  return null;
};

export default function TimelineEvent({ event }) {
  const cfg = CONFIG[event.event_type] || CONFIG.Other;
  const Icon = cfg.icon;
  const { lab, medication: med, source } = event;

  const isActuallyAbnormal = event.abnormal && event.event_type !== 'Family History';
  const dateLabel = event.date || event.original_date_str || 'History (undated)';

  return (
    <div className="relative pl-8 pb-8 border-l-2 border-slate-200 last:border-l-transparent">
      <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-4 border-white shadow-sm ${isActuallyAbnormal ? 'bg-red-500' : 'bg-blue-600'}`} />

      <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${cfg.badge}`}>
              <Icon className="w-4 h-4" /> {event.event_type}
            </span>
            <span className="text-sm text-slate-500 flex items-center gap-1.5 font-semibold">
              <Calendar className="w-4 h-4 text-slate-400" /> {dateLabel}
            </span>
          </div>
          {isActuallyAbnormal && (
            <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg text-red-600 bg-red-50 border border-red-100">
              <AlertCircle className="w-4 h-4" /> Abnormal
            </span>
          )}
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-1">{event.title}</h3>
        <p className="text-slate-600 text-sm leading-relaxed">{event.description}</p>

        {lab && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3 text-sm">
            <span className="font-semibold text-slate-700">{lab.test_name}</span>
            <span className={`font-mono font-bold px-2.5 py-1 rounded-lg border ${lab.status === 'normal' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
              {labDisplay(lab)}
            </span>
            {refDisplay(lab) && <span className="text-xs text-slate-500">Ref: {refDisplay(lab)}</span>}
            <span className="text-xs uppercase font-bold text-slate-400">{lab.status}</span>
          </div>
        )}

        {med && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-slate-700">{med.name}</span>
            {med.dose && <span className="font-mono text-xs bg-slate-50 border border-slate-200 px-2 py-1 rounded-lg">{med.dose}</span>}
            {med.frequency && <span className="font-mono text-xs bg-slate-50 border border-slate-200 px-2 py-1 rounded-lg">{med.frequency}</span>}
            {med.action && med.action !== 'unknown' && (
              <span className={`text-xs font-bold px-2 py-1 rounded-lg border ${ACTION_STYLE[med.action] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                {med.action}
              </span>
            )}
          </div>
        )}

        {source?.source_text && (
          <div className="mt-4 flex items-start gap-2 text-xs text-slate-500 border-l-2 border-slate-200 pl-3">
            <p className="italic flex-1">“{source.source_text}”</p>
            {source.verified ? (
              <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-lg whitespace-nowrap font-semibold">
                <ShieldCheck className="w-3.5 h-3.5" /> Verified{source.page ? ` · p.${source.page}` : ''}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-amber-700 bg-amber-50 border border-amber-200 px-2 py-1 rounded-lg whitespace-nowrap font-semibold">
                <ShieldAlert className="w-3.5 h-3.5" /> Unverified
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}