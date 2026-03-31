import api from './api';
import { Protagonist, ProtagonistCreate } from '../types/api';

export const protagonistService = {
  list: async () => {
    const response = await api.get<Protagonist[]>('/protagonists/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get<Protagonist>(`/protagonists/${id}`);
    return response.data;
  },
  create: async (data: ProtagonistCreate) => {
    const response = await api.post<Protagonist>('/protagonists/', data);
    return response.data;
  },
  update: async (id: number, data: ProtagonistCreate) => {
    const response = await api.put<Protagonist>(`/protagonists/${id}`, data);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`/protagonists/${id}`);
  }
};
