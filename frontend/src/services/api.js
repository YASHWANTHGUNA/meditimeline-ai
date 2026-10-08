import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const parseMedicalReport = async (patientId, reportText) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/parse-report`, {
      patient_id: patientId,
      report_text: reportText,
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to analyze medical report');
  }
};