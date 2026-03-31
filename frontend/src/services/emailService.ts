import api from './api';
import type { EmailThread, EmailThreadDetail, EmailQuote } from '@/types/api';

export const emailService = {
  listThreads: async () => {
    const response = await api.get<EmailThread[]>('/emails/threads');
    return response.data;
  },
  getThread: async (id: number) => {
    const response = await api.get<EmailThreadDetail>(`/emails/threads/${id}`);
    return response.data;
  },
  getEmailQuotes: async (emailId: number) => {
    const response = await api.get<EmailQuote[]>(`/emails/emails/${emailId}/quotes`);
    return response.data;
  },
  deleteThread: async (id: number) => {
    await api.delete(`/emails/threads/${id}`);
  }
};
