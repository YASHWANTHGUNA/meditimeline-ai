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

export const parseMedicalReport = async (patientId, reportText) => {
  try {
    const { data } = await axios.post(`${API_BASE_URL}/api/parse-report`, {
      patient_id: patientId,
      text: reportText, // backend field is `text`, not `report_text`
    });
    return data;
  } catch (error) {
    throw new Error(
      formatError(error.response?.data?.detail) ||
        (error.code === 'ERR_NETWORK' ? 'Cannot reach backend. Is it running on :8000?' : error.message) ||
        'Failed to analyze medical report'
    );
  }
};