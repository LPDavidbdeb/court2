import React, { useEffect, useState } from 'react';
import { emailService } from '../services/emailService';
import type { EmailThread, EmailThreadDetail, EmailQuote } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Mail, User, Calendar, Quote, MessageSquare, Trash2, ArrowLeft } from 'lucide-react';

const EmailInbox: React.FC = () => {
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [selectedThread, setSelectedThread] = useState<EmailThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [threadLoading, setThreadLoading] = useState(false);

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        setLoading(true);
        const data = await emailService.listThreads();
        setThreads(data);
      } catch (error) {
        console.error('Error fetching threads:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchThreads();
  }, []);

  const handleSelectThread = async (id: number) => {
    try {
      setThreadLoading(true);
      const data = await emailService.getThread(id);
      setSelectedThread(data);
    } catch (error) {
      console.error('Error fetching thread detail:', error);
    } finally {
      setThreadLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex gap-6 animate-in fade-in duration-500">
      {/* Thread List */}
      <div className="w-1/3 flex flex-col gap-4">
        <div className="flex items-center justify-between px-1">
          <h1 className="text-2xl font-black tracking-tighter">Inbox</h1>
          <Badge variant="secondary" className="font-bold">{threads.length} Threads</Badge>
        </div>
        
        <Card className="flex-1 overflow-hidden border-slate-200">
          <ScrollArea className="h-full">
            <div className="divide-y divide-slate-100">
              {loading ? (
                Array(5).fill(0).map((_, i) => (
                  <div key={i} className="p-4 space-y-2"><Skeleton className="h-4 w-3/4" /><Skeleton className="h-3 w-1/2" /></div>
                ))
              ) : threads.map(t => (
                <div 
                  key={t.id} 
                  className={`p-4 cursor-pointer transition-all hover:bg-slate-50 ${selectedThread?.id === t.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''}`}
                  onClick={() => handleSelectThread(t.id)}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-black text-blue-600 uppercase tracking-widest">
                      {t.protagonist ? `${t.protagonist.first_name} ${t.protagonist.last_name}` : 'Unknown'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-bold">{new Date(t.updated_at).toLocaleDateString()}</span>
                  </div>
                  <h3 className={`text-sm font-bold truncate ${selectedThread?.id === t.id ? 'text-blue-900' : 'text-slate-800'}`}>
                    {t.subject || '(No Subject)'}
                  </h3>
                </div>
              ))}
            </div>
          </ScrollArea>
        </Card>
      </div>

      {/* Reading Pane */}
      <div className="flex-1 flex flex-col">
        {selectedThread ? (
          <Card className="flex-1 flex flex-col overflow-hidden border-slate-200 shadow-lg">
            <CardHeader className="border-b bg-slate-50/50 py-4">
              <div className="flex justify-between items-center">
                <CardTitle className="text-xl font-black text-slate-900">{selectedThread.subject}</CardTitle>
                <div className="flex gap-2">
                  <Button variant="ghost" size="icon" className="text-red-500 hover:text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
            </CardHeader>
            <ScrollArea className="flex-1">
              <CardContent className="p-6 space-y-8">
                {selectedThread.emails.map((email, idx) => (
                  <div key={email.id} className="space-y-4 relative">
                    {idx > 0 && <div className="absolute -top-4 left-0 right-0 border-t border-dashed border-slate-100" />}
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 border">
                          <User className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-xs font-black text-slate-900 uppercase tracking-tight">
                            {email.sender_protagonist ? `${email.sender_protagonist.first_name} ${email.sender_protagonist.last_name}` : email.sender}
                          </p>
                          <p className="text-[10px] text-slate-400 font-medium">{new Date(email.date_sent || '').toLocaleString()}</p>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-[9px] font-bold">MESSAGE #{idx + 1}</Badge>
                    </div>
                    
                    <div className="bg-white p-4 rounded-lg border border-slate-100 shadow-sm whitespace-pre-wrap text-sm text-slate-700 leading-relaxed font-sans">
                      {email.body_plain_text}
                    </div>

                    {/* Placeholder for Quotes - would be fetched per email in a real scenario or passed in detail */}
                    <div className="pl-4 space-y-2">
                       <div className="flex items-center gap-2 text-blue-600 mb-1">
                         <Quote className="h-3 w-3" />
                         <span className="text-[10px] font-black uppercase tracking-widest">Marked Excerpts</span>
                       </div>
                       <p className="text-[11px] text-slate-400 italic">No quotes extracted for this message yet.</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </ScrollArea>
          </Card>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
            <Mail className="h-12 w-12 text-slate-200 mb-4" />
            <p className="text-slate-400 font-bold uppercase text-xs tracking-widest">Select a thread to view correspondence</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailInbox;
