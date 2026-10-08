import React from 'react';
import { AlertCircle, Calendar, Pill, Activity, Stethoscope, FileText, Building2, Syringe } from 'lucide-react';

export default function TimelineEvent({ event }) {
  const getEventConfig = (type) => {
    switch (type) {
      case 'Diagnosis': return { badge: 'bg-purple-100 text-purple-700', icon: <Activity className="w-4 h-4 text-purple-600" /> };
      case 'Medication': return { badge: 'bg-green-100 text-green-700', icon: <Pill className="w-4 h-4 text-green-600" /> };
      case 'Lab Result': return { badge: 'bg-amber-100 text-amber-700', icon: <FileText className="w-4 h-4 text-amber-600" /> };
      case 'Hospital Visit': return { badge: 'bg-blue-100 text-blue-700', icon: <Building2 className="w-4 h-4 text-blue-600" /> };
      case 'Procedure': return { badge: 'bg-cyan-100 text-cyan-700', icon: <Syringe className="w-4 h-4 text-cyan-600" /> };
      default: return { badge: 'bg-slate-100 text-slate-700', icon: <Stethoscope className="w-4 h-4 text-slate-600" /> };
    }
  };

  const config = getEventConfig(event.event_type);

  return (
    <div className="relative pl-8 pb-10 border-l-2 border-slate-200 last:border-l-0 last:pb-0 group">
      {/* Node */}
      <div className="absolute -left-[11px] top-1 w-5 h-5 rounded-full border-4 border-white bg-blue-600 shadow-sm transition-transform group-hover:scale-125" />

      <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <span className={`text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 ${config.badge}`}>
              {config.icon}
              {event.event_type}
            </span>
            <span className="text-sm text-slate-500 flex items-center gap-1.5 font-semibold">
              <Calendar className="w-4 h-4 text-slate-400" />
              {event.date}
            </span>
          </div>

          {event.abnormal && (
            <span className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg text-red-600 bg-red-50 border border-red-100">
              <AlertCircle className="w-4 h-4" />
              Abnormal Finding
            </span>
          )}
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-2">{event.title}</h3>
        <p className="text-slate-600 leading-relaxed text-sm mb-4">{event.description}</p>

        {event.medications && event.medications.length > 0 && (
          <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 text-slate-700 font-semibold text-sm mr-2">
              <Pill className="w-4 h-4 text-blue-600" />
              <span>Medications:</span>
            </div>
            {event.medications.map((med, idx) => (
              <span key={idx} className="bg-slate-50 px-3 py-1 rounded-lg border border-slate-200 font-mono text-xs font-semibold text-slate-700">
                {med}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}