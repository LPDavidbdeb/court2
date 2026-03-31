import api from './api';
import type { Document, DocumentCreate } from '@/types/api';

export const documentService = {
  list: async () => {
    const response = await api.get<Document[]>('/documents/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get<Document>(`/documents/${id}`);
    return response.data;
  },
  create: async (data: DocumentCreate) => {
    const response = await api.post<Document>('/documents/', data);
    return response.data;
  },
  update: async (id: number, data: DocumentCreate) => {
    const response = await api.put<Document>(`/documents/${id}`, data);
    return response.data;
  },
  getTree: async (id: number) => {
    const response = await api.get<any[]>(`/documents/${id}/tree`);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`/documents/${id}`);
  }
};