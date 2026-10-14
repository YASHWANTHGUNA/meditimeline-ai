import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// FastAPI 422 returns detail as an array of {loc, msg, type}
const formatError = (detail) => {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ');
  }
  return JSON.stringify(detail);
};

const toError = (error, fallback) =>
  new Error(
    formatError(error.response?.data?.detail) ||
      (error.code === 'ERR_NETWORK' ? `Cannot reach backend at ${API_BASE_URL}. Is it running?` : error.message) ||
      fallback
  );

export const parseMedicalReport = async (patientId, reportText) => {
  try {
    const payload = { text: reportText };
    if (patientId && patientId.trim()) {
      payload.patient_id = patientId.trim();
    }
    const { data } = await axios.post(`${API_BASE_URL}/api/parse-report`, payload);
    return data;
  } catch (error) {
    throw toError(error, 'Failed to analyze medical report');
  }
};

export const uploadMedicalReport = async (file, patientId = null) => {
  const form = new FormData();
  form.append('file', file);
  if (patientId && (typeof patientId === 'string' ? patientId.trim() : true)) {
    form.append('patient_id', typeof patientId === 'string' ? patientId.trim() : patientId);
  }
  try {
    // Do NOT set Content-Type manually: the browser adds the multipart boundary.
    // Long timeout: multi-page PDFs make several Gemini calls.
    const { data } = await axios.post(`${API_BASE_URL}/api/upload-report`, form, { timeout: 180000 });
    return data;
  } catch (error) {
    throw toError(error, 'Failed to analyze PDF');
  }
};

export const getRiskFlags = async (patientId) => {
  try {
    const { data } = await axios.get(`${API_BASE_URL}/patients/${encodeURIComponent(patientId)}/risk-flags`);
    return data;
  } catch (error) {
    throw toError(error, 'Failed to load preventive insights');
  }
};