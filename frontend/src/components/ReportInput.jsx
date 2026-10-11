import React, { useState, useRef } from 'react';
import { User, Sparkles, FileText, Upload, X } from 'lucide-react';
import { parseMedicalReport, uploadMedicalReport } from '../services/api';

const MAX_MB = 10;

export default function ReportInput({ onAnalysisComplete, setIsLoading, setError }) {
  const [patientId, setPatientId] = useState('');
  const [mode, setMode] = useState('pdf'); // 'pdf' | 'text'
  const [reportText, setReportText] = useState('');
  const [file, setFile] = useState(null);
  const [notice, setNotice] = useState(null);
  const fileRef = useRef(null);

  const pickFile = (f) => {
    setError(null);
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.pdf')) return setError('Please choose a PDF file.');
    if (f.size > MAX_MB * 1024 * 1024) return setError(`PDF is too large (max ${MAX_MB} MB).`);
    setFile(f);
  };

  const clearFile = () => {
    setFile(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setNotice(null);

    if (mode === 'text' && !reportText.trim()) return setError('Please enter medical report text.');
    if (mode === 'pdf' && !file) return setError('Please choose a PDF report to upload.');

    setIsLoading(true);
    try {
      const pid = patientId.trim();
      
      const data =
        mode === 'pdf' 
          ? await uploadMedicalReport(file, pid || null) 
          : await parseMedicalReport(pid || null, reportText);

      // Robust extraction: Checks all_events, dated/undated combined, or flat events
      const timelineObj = data?.timeline || data;
      const events = 
        timelineObj?.all_events ?? 
        ((timelineObj?.dated_events || timelineObj?.undated_events) 
          ? [...(timelineObj?.dated_events || []), ...(timelineObj?.undated_events || [])] 
          : null) ?? 
        data?.events ?? 
        [];

      if (!Array.isArray(events) || events.length === 0) {
        onAnalysisComplete(null);
        setError(data?.message || 'No clinical events were extracted. Try a more detailed report.');
        return;
      }
      if (data.duplicate) setNotice(data.message);
      onAnalysisComplete(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const tab = (id, label, Icon) => (
    <button
      type="button"
      onClick={() => setMode(id)}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
        mode === id ? 'bg-blue-600 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
      }`}
    >
      <Icon className="w-4 h-4" /> {label}
    </button>
  );

  return (
    <div className="bg-white p-8 md:p-10 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 mb-10">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Clinical Record Ingestion</h2>
        <p className="text-slate-500 text-sm">
          Upload a digital PDF report or paste text. Everything is merged into one patient timeline.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="max-w-xs">
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Patient Identifier <span className="text-xs text-slate-400 font-normal ml-1">(Optional)</span>
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <User className="w-5 h-5 text-slate-400" />
            </span>
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-900 font-medium transition-all"
              placeholder="Auto-extracted if blank"
            />
          </div>
        </div>

        <div className="flex gap-2">
          {tab('pdf', 'Upload PDF', Upload)}
          {tab('text', 'Paste Text', FileText)}
        </div>

        {mode === 'pdf' ? (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              pickFile(e.dataTransfer.files?.[0]);
            }}
            onClick={() => !file && fileRef.current?.click()}
            className="border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-2xl p-10 text-center cursor-pointer transition-colors bg-slate-50"
          >
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <span className="font-semibold text-slate-800">{file.name}</span>
                <span className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    clearFile();
                  }}
                  className="p-1 rounded-full hover:bg-slate-200"
                  aria-label="Remove file"
                >
                  <X className="w-4 h-4 text-slate-500" />
                </button>
              </div>
            ) : (
              <>
                <Upload className="w-8 h-8 mx-auto text-slate-400 mb-3" />
                <p className="text-sm font-semibold text-slate-700">Click to choose or drag & drop a PDF</p>
                <p className="text-xs text-slate-500 mt-1">Digital (text-based) PDFs up to {MAX_MB} MB</p>
              </>
            )}
          </div>
        ) : (
          <textarea
            rows={6}
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            className="w-full p-5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-700 font-mono text-sm leading-relaxed transition-all placeholder:text-slate-400"
            placeholder="Paste doctor notes, prescriptions, diagnostic summaries, or lab results here..."
          />
        )}

        {notice && (
          <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">{notice}</p>
        )}

        <div className="pt-2">
          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3.5 rounded-xl text-sm font-bold tracking-wide transition-all duration-200 flex items-center gap-2 shadow-lg shadow-blue-600/20 active:scale-95"
          >
            <Sparkles className="w-5 h-5" /> Generate Health Timeline
          </button>
        </div>
      </form>
    </div>
  );
}
