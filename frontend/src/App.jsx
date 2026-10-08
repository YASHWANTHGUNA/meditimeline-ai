import React, { useState } from 'react';
import ReportInput from './components/ReportInput';
import Timeline from './components/Timeline';
import { Activity, AlertCircle, Loader2 } from 'lucide-react';

export default function App() {
  const [timelineData, setTimelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Clean White Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white p-2 rounded-xl shadow-md shadow-blue-600/20">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight leading-none">
                MediTimeline <span className="text-blue-600">AI</span>
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl w-full mx-auto px-6 py-10 flex-1">
        <ReportInput 
          onAnalysisComplete={setTimelineData} 
          setIsLoading={setIsLoading} 
          setError={setError} 
        />

        {error && (
          <div className="bg-red-50 p-4 rounded-2xl mb-8 flex items-center gap-3 text-sm border border-red-100 text-red-600 shadow-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        {isLoading && (
          <div className="bg-white p-16 rounded-3xl border border-slate-100 flex flex-col items-center justify-center text-center my-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
            <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
            <h3 className="font-bold text-lg text-slate-900 mb-1">Processing Medical Records</h3>
            <p className="text-sm text-slate-500">Extracting clinical events and building chronological timeline...</p>
          </div>
        )}

        {!isLoading && timelineData && (
          <Timeline timelineData={timelineData} />
        )}
      </main>
    </div>
  );
}