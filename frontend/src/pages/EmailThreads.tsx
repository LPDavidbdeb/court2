import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Mail, ArrowLeft } from 'lucide-react';

interface EmailThread {
  id: number;
  thread_id: str;
  subject: string;
  protagonist?: {
    first_name: string;
    last_name: string;
  };
  updated_at: string;
}

const EmailThreadsView: React.FC = () => {
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const response = await api.get('/emails/threads');
        setThreads(response.data);
      } catch (err) {
        console.error("Failed to fetch email threads", err);
      } finally {
        setLoading(false);
      }
    };
    fetchThreads();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-4">
        <Skeleton className="h-10 w-[250px]" />
        <Card>
          <CardHeader><Skeleton className="h-6 w-1/3" /></CardHeader>
          <CardContent><Skeleton className="h-[400px] w-full" /></CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
        </Button>
        <h1 className="text-2xl font-bold">Email Management</h1>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center space-x-4">
          <div className="p-2 bg-blue-100 rounded-full">
            <Mail className="h-6 w-6 text-blue-600" />
          </div>
          <CardTitle>Email Threads</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Protagonist</TableHead>
                <TableHead>Last Updated</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {threads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                    No email threads found.
                  </TableCell>
                </TableRow>
              ) : (
                threads.map((thread) => (
                  <TableRow key={thread.id}>
                    <TableCell className="font-medium">{thread.subject || '(No Subject)'}</TableCell>
                    <TableCell>
                      {thread.protagonist ? `${thread.protagonist.first_name} ${thread.protagonist.last_name}` : 'N/A'}
                    </TableCell>
                    <TableCell>{new Date(thread.updated_at).toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/emails/threads/${thread.id}`}>
                        <Button variant="ghost" size="sm">View Thread</Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default EmailThreadsView;
