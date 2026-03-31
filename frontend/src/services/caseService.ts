import api from './api';
import type { LegalCase, LegalCaseDetail, PerjuryContestation } from '@/types/api';

export const caseService = {
  list: async () => {
    const response = await api.get<LegalCase[]>('/cases/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get<LegalCaseDetail>(`/cases/${id}`);
    return response.data;
  },
  create: async (data: { title: string }) => {
    const response = await api.post<LegalCase>('/cases/', data);
    return response.data;
  },
  update: async (id: number, data: { title: string }) => {
    const response = await api.put<LegalCase>(`/cases/${id}`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`/cases/${id}`);
  },
  
  // Contestations
  listContestations: async (caseId: number) => {
    const response = await api.get<PerjuryContestation[]>(`/cases/${caseId}/contestations`);
    return response.data;
  },
  createContestation: async (caseId: number, data: any) => {
    const response = await api.post<PerjuryContestation>(`/cases/${caseId}/contestations`, data);
    return response.data;
  },
  updateContestation: async (id: number, data: any) => {
    const response = await api.put<PerjuryContestation>(`/cases/contestations/${id}`, data);
    return response.data;
  },
  deleteContestation: async (id: number) => {
    await api.delete(`/cases/contestations/${id}`);
  }
};
