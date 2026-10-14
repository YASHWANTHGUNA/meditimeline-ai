import React, { useMemo, useState } from 'react';
import TimelineEvent from './TimelineEvent';
import { Activity, User } from 'lucide-react';

const FILTERS = [
  { id: 'all', label: 'All', test: () => true },
  { id: 'abnormal', label: 'Abnormal', test: (e) => e.abnormal && e.event_type !== 'Family History' },
  { id: 'labs', label: 'Labs', test: (e) => e.event_type === 'Lab Result' },
  { id: 'vitals', label: 'Vitals', test: (e) => e.event_type === 'Vital Sign' },
  { id: 'meds', label: 'Medications', test: (e) => e.event_type === 'Medication' },
  { id: 'dx', label: 'Diagnoses', test: (e) => e.event_type === 'Diagnosis' },
];

export default function Timeline({ timelineData }) {
  const [filter, setFilter] = useState('all');

  const timelineObj = timelineData?.timeline || timelineData;
  const events = useMemo(() => {
    const e =
      timelineObj?.all_events ??
      (timelineObj?.dated_events || timelineObj?.undated_events
        ? [...(timelineObj?.dated_events || []), ...(timelineObj?.undated_events || [])]
        : null) ??
      timelineData?.events ??
      [];
    return Array.isArray(e) ? e : [];
  }, [timelineData, timelineObj]);

  const counts = useMemo(
    () => Object.fromEntries(FILTERS.map((f) => [f.id, events.filter(f.test).length])),
    [events]
  );
  const visible = useMemo(
    () => events.filter((FILTERS.find((f) => f.id === filter) || FILTERS[0]).test),
    [events, filter]
  );

  if (events.length === 0) {
    return (
      <div className="bg-white p-6 rounded-2xl border border-slate-200 text-slate-600">
        No clinical events are available to display.
      </div>
    );
  }

  return (
    <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-5 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-100 text-blue-600">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Chronological Patient Health Timeline</h2>
            <p className="text-xs text-slate-500">
              {events.length} events · normalized, sorted and source-verified
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-700">
          <User className="w-3.5 h-3.5 text-blue-600" />
          Patient ID: {timelineData?.patient_id ?? 'Unknown'}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-8">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFilter(f.id)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === f.id
                ? f.id === 'abnormal' ? 'bg-red-600 text-white shadow' : 'bg-blue-600 text-white shadow'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {f.label} <span className="opacity-70">({counts[f.id]})</span>
          </button>
        ))}
      </div>

      <div className="ml-4 space-y-2">
        {visible.length === 0 ? (
          <p className="text-sm text-slate-500">No events match this filter.</p>
        ) : (
          visible.map((event, i) => <TimelineEvent key={event.event_id ?? i} event={event} />)
        )}
      </div>
    </div>
  );
}