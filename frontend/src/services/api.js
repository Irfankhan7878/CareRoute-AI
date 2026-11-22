import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000,
});

export const api = {
  // Intake & Processing
  submitIntake: async (payload) => {
    const res = await apiClient.post('/api/intake', payload);
    return res.data;
  },

  processIntake: async (payload) => {
    const res = await apiClient.post('/api/process', payload);
    return res.data;
  },

  // Departments
  getDepartments: async () => {
    const res = await apiClient.get('/api/departments');
    return res.data;
  },

  getDepartment: async (idOrCode) => {
    const res = await apiClient.get(`/api/departments/${idOrCode}`);
    return res.data;
  },

  // Appointments
  getAvailableAppointments: async (departmentCode, date = null) => {
    const params = { department_code: departmentCode };
    if (date) params.date = date;
    const res = await apiClient.get('/api/appointments/available', { params });
    return res.data;
  },

  bookAppointment: async (slotId, patientId, patientName) => {
    const res = await apiClient.post('/api/appointments/book', {
      slot_id: slotId,
      patient_id: patientId,
      patient_name: patientName,
    });
    return res.data;
  },

  // Patient Memory & History
  getPatientHistory: async (patientId) => {
    const res = await apiClient.get(`/api/patients/${patientId}/history`);
    return res.data;
  },

  // Agent System & Admin
  getAgentStatus: async () => {
    const res = await apiClient.get('/api/agents/status');
    return res.data;
  },

  getExecutionTrace: async (executionId) => {
    const res = await apiClient.get(`/api/executions/${executionId}`);
    return res.data;
  },

  getAdminDashboard: async () => {
    const res = await apiClient.get('/api/admin/dashboard');
    return res.data;
  },

  getHealth: async () => {
    const res = await apiClient.get('/api/health');
    return res.data;
  },
};

export default api;
