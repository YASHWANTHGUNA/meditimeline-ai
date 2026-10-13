import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, Siren, Loader2 } from 'lucide-react';
import { getRiskFlags } from '../api';

const LEVEL = {
  routine: { label: 'Routine follow-up', box: 'bg-emerald-50 border-emerald-200 text-emerald-800', chip: 'bg-emerald-100 text-emerald-700', icon: ShieldCheck },
  soon: { label: 'See a clinician soon', box: 'bg-amber-50 border-amber-200 text-amber-800', chip: 'bg-amber-100 text-amber-700', icon: AlertTriangle },
  prompt: { label: 'Seek prompt evaluation', box: 'bg-red-50 border-red-200 text-red-800', chip: 'bg-red-100 text-red-700', icon: Siren },
};

export default function RiskPanel({ patientId, refreshKey }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!patientId) return;
    let alive = true;
    setData(null); setError(null);
    getRiskFlags(patientId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setError('Could not compute preventive insights.'));
    return () => { alive = false; };
  }, [patientId, refreshKey]);

  if (!patientId) return null;
  if (error) return <div className="bg-white p-4 rounded-2xl border border-slate-200 text-sm text-slate-600">{error}</div>;
  if (!data) return <div className="bg-white p-4 rounded-2xl border border-slate-200 text-sm text-slate-500 flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Analysing preventive risk…</div>;

  const cfg = LEVEL[data.overall_level] || LEVEL.routine;
  const Icon = cfg.icon;
  return (
    <div className="bg-white p-6 rounded-3xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] mb-6">
      <div className={`flex items-start gap-3 p-4 rounded-2xl border ${cfg.box}`}>
        <Icon className="w-6 h-6 mt-0.5 shrink-0" />
        <div>
          <h2 className="font-bold">Preventive Health Insights · {cfg.label}</h2>
          <p className="text-sm">{data.summary}</p>
        </div>
      </div>

      {data.flags.length > 0 && (
        <ul className="mt-4 space-y-3">
          {data.flags.map((f, i) => {
            const c = LEVEL[f.level] || LEVEL.routine;
            return (
              <li key={i} className="border border-slate-100 rounded-xl p-4">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${c.chip}`}>{f.category}</span>
                  {f.date && <span className="text-xs text-slate-500">{f.date}</span>}
                </div>
                <p className="text-sm font-semibold text-slate-800">{f.finding}</p>
                <p className="text-sm text-slate-600 mt-1">→ {f.recommendation}</p>
              </li>
            );
          })}
        </ul>
      )}
      <p className="mt-4 text-xs text-slate-500 italic">{data.disclaimer}</p>
    </div>
  );
}