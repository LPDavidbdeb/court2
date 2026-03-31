import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

interface ProtagonistSummary {
  id: number;
  first_name: string;
  last_name: string | null;
  role: string;
}

interface EmailThread {
  id: number;
  thread_id: string;
  subject: string | null;
  start_date: string | null;
  saved_at: string;
  updated_at: string;
  protagonist: ProtagonistSummary | null;
}

function fullName(p: ProtagonistSummary | null): string {
  if (!p) return 'N/A';
  return `${p.first_name} ${p.last_name ?? ''}`.trim() || 'N/A';
}

export default function EmailThreadList() {
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchThreads = () => {
    api.get('/emails/threads/')
      .then(res => setThreads(res.data))
      .catch(() => setError('Failed to load email threads.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchThreads(); }, []);

  const handleDelete = async (thread: EmailThread) => {
    if (!confirm(`Are you sure you want to delete this entire thread? This action cannot be undone.\n\n"${thread.subject ?? '(No Subject)'}"`)) return;
    try {
      await api.delete(`/emails/threads/${thread.id}/`);
      setThreads(prev => prev.filter(t => t.id !== thread.id));
    } catch {
      alert('Failed to delete thread.');
    }
  };

  const formatDate = (iso: string | null) =>
    iso ? new Date(iso).toLocaleString('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace('T', ' ') : 'N/A';

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="max-w-6xl">
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between py-4">
          <CardTitle className="text-lg font-bold">Saved Email Threads</CardTitle>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigate('/emails/upload')}
            >
              Upload EML
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {threads.length === 0 ? (
            <div className="p-6 text-slate-500">No email threads have been saved yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200">
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Start Date</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Associated Protagonist</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Thread Subject</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {threads.map((thread, i) => (
                    <tr
                      key={thread.id}
                      className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}
                    >
                      <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                        {formatDate(thread.start_date)}
                      </td>
                      <td className="px-4 py-3 text-slate-700">
                        {fullName(thread.protagonist)}
                      </td>
                      <td className="px-4 py-3 max-w-sm">
                        <Link
                          to={`/emails/threads/${thread.id}`}
                          className="text-primary hover:underline font-medium"
                        >
                          {(thread.subject ?? '(No Subject)').slice(0, 70)}
                          {(thread.subject ?? '').length > 70 ? '…' : ''}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <Link to={`/emails/threads/${thread.id}`}>
                            <Button size="sm" variant="outline" className="text-sky-600 border-sky-300 hover:bg-sky-50">
                              View
                            </Button>
                          </Link>
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-red-600 border-red-300 hover:bg-red-50"
                            onClick={() => handleDelete(thread)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
