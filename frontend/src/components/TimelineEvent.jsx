import React from 'react';
import { AlertCircle, Calendar, Pill, Activity, Stethoscope, FileText, Building2, Syringe, HeartPulse, FlaskConical } from 'lucide-react';

const CONFIG = {
  Diagnosis:  { badge: 'bg-purple-100 text-purple-700', icon: Activity },
  Medication: { badge: 'bg-green-100 text-green-700',  icon: Pill },
  'Lab Result': { badge: 'bg-amber-100 text-amber-700', icon: FlaskConical },
  Visit:      { badge: 'bg-blue-100 text-blue-700',    icon: Building2 },
  Procedure:  { badge: 'bg-cyan-100 text-cyan-700',    icon: Syringe },
  Symptom:    { badge: 'bg-rose-100 text-rose-700',    icon: HeartPulse },
  Other:      { badge: 'bg-slate-100 text-slate-700',  icon: Stethoscope },
};

const ACTION_STYLE = {
  started: 'bg-green-50 text-green-700 border-green-200',
  increased: 'bg-orange-50 text-orange-700 border-orange-200',
  decreased: 'bg-sky-50 text-sky-700 border-sky-200',
  stopped: 'bg-red-50 text-red-700 border-red-200',
};

export default function TimelineEvent({ event }) {
  const cfg = CONFIG[event.event_type] || CONFIG.Other;
  const Icon = cfg.icon;
  const { lab, medication: med } = event;

  return (
    <div className="relative pl-8 pb-8 border-l-2 border-slate-200 last:border-l-transparent group">
      <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-4 border-white shadow-sm ${event.abnormal ? 'bg-red-500' : 'bg-blue-600'}`} />

      <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${cfg.badge}`}>
              <Icon className="w-4 h-4" /> {event.event_type}
            </span>
            <span className="text-sm text-slate-500 flex items-center gap-1.5 font-semibold">
              <Calendar className="w-4 h-4 text-slate-400" />
              {event.date || event.original_date_str || 'Undated'}
            </span>
          </div>
          {event.abnormal && (
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
              {lab.value ?? lab.value_text} {lab.unit}
            </span>
            {(lab.reference_low != null || lab.reference_high != null) && (
              <span className="text-xs text-slate-500">
                Ref: {lab.reference_low ?? '–'} – {lab.reference_high ?? '–'} {lab.unit}
              </span>
            )}
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

        {event.source?.source_text && (
          <p className="mt-4 text-xs text-slate-400 italic border-l-2 border-slate-200 pl-3">
            “{event.source.source_text}”
          </p>
        )}
      </div>
    </div>
  );
}