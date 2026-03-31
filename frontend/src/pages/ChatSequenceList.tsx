import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { MessageSquare, Eye, Trash2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface ChatSequence {
  id: number;
  title: string;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  message_count: number;
}

export default function ChatSequenceList() {
  const [sequences, setSequences] = useState<ChatSequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/chats/sequences/')
      .then(res => {
        setSequences(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch sequences:', err);
        setError('Failed to load sequences.');
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading sequences...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Evidence Sequences</h1>
          <p className="text-slate-500">Curated chat excerpts linked to case themes.</p>
        </div>
        <Link 
          to="/chats/stream"
          className={cn(buttonVariants({ variant: 'default' }))}
        >
          <MessageSquare className="h-4 w-4 mr-2" /> Open Stream
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {sequences.length === 0 ? (
          <div className="text-center py-12 bg-white border-2 border-dashed border-slate-100 rounded-xl text-slate-400 italic">
            No sequences created yet.
          </div>
        ) : (
          sequences.map(seq => (
            <Card key={seq.id} className="shadow-sm border-slate-200 hover:border-primary/30 transition-colors">
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="space-y-1 flex-1">
                    <Link to={`/chats/sequences/${seq.id}`} className="text-lg font-bold text-slate-900 hover:text-primary transition-colors">
                      {seq.title}
                    </Link>
                    <div className="flex items-center gap-4 text-xs text-slate-500 font-medium uppercase tracking-wider">
                       <span>{seq.message_count} messages</span>
                       {seq.start_date && (
                         <span>{new Date(seq.start_date).toLocaleDateString()} — {new Date(seq.end_date!).toLocaleDateString()}</span>
                       )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Link 
                      to={`/chats/sequences/${seq.id}`}
                      className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                    >
                      <Eye className="h-4 w-4 mr-2" /> View Sequence
                    </Link>
                    <Button variant="ghost" size="sm" className="text-slate-400 hover:text-red-500" disabled>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
