import React, { useState } from 'react';
import { FileText, User, Sparkles } from 'lucide-react';

export default function ReportInput({ onAnalysisComplete, setIsLoading, setError }) {
  const [patientId, setPatientId] = useState('P001');
  const [reportText, setReportText] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reportText.trim()) return setError('Please enter medical report text.');
    
    setIsLoading(true);
    setError(null);
    try {
      const data = await import('../services/api').then(mod => mod.parseMedicalReport(patientId, reportText));
      onAnalysisComplete(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 md:p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 mb-10">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Clinical Record Ingestion</h2>
        <p className="text-slate-500 text-sm">Securely parse fragmented medical histories, prescriptions, and lab results into a structured timeline.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="max-w-xs">
          <label className="block text-sm font-semibold text-slate-700 mb-2">Patient Identifier</label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <User className="w-5 h-5 text-slate-400" />
            </span>
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-900 font-medium transition-all"
              placeholder="e.g. P001"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Unstructured Medical Report Text
          </label>
          <textarea
            rows={6}
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            className="w-full p-5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-700 font-mono text-sm leading-relaxed transition-all placeholder:text-slate-400"
            placeholder="Paste doctor notes, prescriptions, diagnostic summaries, or lab results here..."
            required
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl text-sm font-bold tracking-wide transition-all duration-200 flex items-center gap-2 shadow-lg shadow-blue-600/20 active:scale-95"
          >
            <Sparkles className="w-5 h-5" />
            Generate Health Timeline
          </button>
        </div>
      </form>
    </div>
  );
}