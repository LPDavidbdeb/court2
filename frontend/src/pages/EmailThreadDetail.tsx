import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, User, Calendar, MessageSquare } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Email {
  id: number;
  subject: string;
  sender: string;
  date_sent: string;
  body_plain_text: string;
  sender_protagonist?: {
    first_name: string;
    last_name: string;
    role: string;
  };
}

interface ThreadDetail {
  id: number;
  subject: string;
  emails: Email[];
}

const EmailThreadDetailView: React.FC = () => {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchThreadDetail = async () => {
      try {
        const response = await api.get(`/emails/threads/${threadId}`);
        setThread(response.data);
      } catch (err) {
        console.error("Failed to fetch thread details", err);
      } finally {
        setLoading(false);
      }
    };
    if (threadId) fetchThreadDetail();
  }, [threadId]);

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-4">
        <Skeleton className="h-10 w-[200px]" />
        <Skeleton className="h-[200px] w-full" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!thread) return <div className="container mx-auto p-6 text-center">Thread not found.</div>;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate('/emails/threads')}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Threads
      </Button>

      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">{thread.subject || '(No Subject)'}</h1>
        <div className="flex items-center gap-2 text-muted-foreground">
          <MessageSquare className="h-4 w-4" />
          <span>{thread.emails.length} Messages in this conversation</span>
        </div>
      </div>

      <div className="space-y-6">
        {thread.emails.map((email, index) => (
          <Card key={email.id} className="overflow-hidden border-l-4 border-l-blue-500">
            <CardHeader className="bg-slate-50/50">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-slate-500" />
                    <span className="font-semibold">
                      {email.sender_protagonist 
                        ? `${email.sender_protagonist.first_name} ${email.sender_protagonist.last_name}`
                        : email.sender}
                    </span>
                    {email.sender_protagonist?.role && (
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {email.sender_protagonist.role}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    <span>{new Date(email.date_sent).toLocaleString()}</span>
                  </div>
                </div>
                <Badge variant="secondary" className="font-mono text-[10px]">
                  #{index + 1}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap font-sans text-slate-700">
                {email.body_plain_text || '(Empty Body)'}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default EmailThreadDetailView;
