import React from 'react';
import TimelineEvent from './TimelineEvent';
import { Activity, Clock } from 'lucide-react';

export default function Timeline({ timelineData }) {
  // Backend returns events inside timeline.all_events.
  // Keep the fallback for compatibility with a flat events response.
  const events =
    timelineData?.timeline?.all_events ??
    timelineData?.events ??
    [];

  if (!Array.isArray(events) || events.length === 0) {
    return (
      <div className="bg-white p-6 rounded-2xl border border-slate-200 text-slate-600">
        No clinical events are available to display.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-800/80 shadow-2xl">
      <div className="flex items-center justify-between mb-8 pb-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Chronological Patient Health Timeline
            </h2>
            <p className="text-xs text-slate-400">
              Normalized and sorted clinical event history
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 text-xs font-medium text-cyan-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Patient ID: {timelineData?.patient_id ?? 'Unknown'}</span>
        </div>
      </div>

      <div className="ml-4 space-y-2">
        {events.map((event, index) => (
          <TimelineEvent
            key={event.event_id ?? index}
            event={event}
          />
        ))}
      </div>
    </div>
  );
}