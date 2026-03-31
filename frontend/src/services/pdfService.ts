import api from './api';
import type { PDFDocument, PDFQuote } from '@/types/api';

export const pdfService = {
  list: async () => {
    const response = await api.get<PDFDocument[]>('/pdfs/');
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get<PDFDocument>(`/pdfs/${id}`);
    return response.data;
  },
  getQuotes: async (pdfId: number) => {
    const response = await api.get<PDFQuote[]>(`/pdfs/${pdfId}/quotes`);
    return response.data;
  },
  delete: async (id: number) => {
    await api.delete(`/pdfs/${id}`);
  }
};
