import React from "react";
import TimelineEvent from "./TimelineEvent";

export default function Timeline({ events = [] }) {
  if (!events || events.length === 0) {
    return (
      <div className="flex items-center justify-center p-12 bg-slate-50 rounded-2xl border border-slate-200 border-dashed">
        <p className="text-slate-500 font-medium">
          No timeline events available.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Patient Timeline</h2>
        <p className="text-slate-500 text-sm mt-1">
          Chronological medical history and events
        </p>
      </div>

      <div className="relative">
        {/* Main Timeline Line */}
        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-slate-200" />

        <div className="space-y-0">
          {events.map((event, index) => (
            <TimelineEvent key={event.id || index} event={event} />
          ))}
        </div>
      </div>
    </div>
  );
}
