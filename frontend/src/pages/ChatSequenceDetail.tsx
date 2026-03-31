import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  ChevronLeft, 
  MessageSquare, 
  Calendar,
  User,
  ExternalLink,
  Trash2
} from 'lucide-react';
import { cn } from '../lib/utils';

interface ChatParticipant {
  id: number;
  name: string | null;
  email: string | null;
}

interface ChatMessage {
  id: number;
  sender: ChatParticipant | null;
  timestamp: string;
  text_content: string | null;
}

interface ChatSequence {
  id: number;
  title: string;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
  messages: ChatMessage[];
}

const SELF_NAME = "Louis Philippe David";

export default function ChatSequenceDetail() {
  const { sequenceId } = useParams<{ sequenceId: string }>();
  const [seq, setSeq] = useState<ChatSequence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(`/chats/sequences/${sequenceId}/`)
      .then(res => {
        setSeq(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch sequence details:', err);
        setError('Failed to load sequence details.');
        setLoading(false);
      });
  }, [sequenceId]);

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading sequence...</div>;
  if (error || !seq) return <div className="p-8 text-center text-red-500">{error || 'Sequence not found.'}</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link 
          to="/chats/sequences"
          className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), "text-slate-500 hover:text-slate-900")}
        >
          <ChevronLeft className="h-5 w-5 mr-1" /> Back to Sequences
        </Link>
        <div className="flex items-center gap-2">
           <Button variant="ghost" size="sm" className="text-red-500" disabled>
             <Trash2 className="h-4 w-4 mr-2" /> Delete
           </Button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
        <div className="bg-slate-50/50 border-b border-slate-100 p-6">
          <div className="flex items-center gap-2 text-primary text-xs font-bold uppercase tracking-widest mb-2">
             <MessageSquare className="h-4 w-4" /> Evidence Sequence
          </div>
          <h1 className="text-2xl font-bold text-slate-900">{seq.title}</h1>
          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
             <div className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                {seq.start_date ? `${new Date(seq.start_date).toLocaleDateString()} — ${new Date(seq.end_date!).toLocaleDateString()}` : 'No date range'}
             </div>
             <div className="flex items-center gap-1.5">
                <Badge variant="secondary" className="bg-slate-200 text-slate-600 border-none font-bold">
                  {seq.messages.length} Messages
                </Badge>
             </div>
          </div>
        </div>

        <div className="p-6 bg-slate-100/30 space-y-6">
          {seq.messages.map(msg => {
            const isSelf = msg.sender?.name === SELF_NAME;
            return (
              <div 
                key={msg.id} 
                className={cn(
                  "flex flex-col max-w-[85%]",
                  isSelf ? "ml-auto items-end" : "items-start"
                )}
              >
                <div className={cn(
                  "mb-1 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400",
                  isSelf ? "flex-row-reverse" : "flex-row"
                )}>
                  <User className="h-3 w-3" />
                  {msg.sender?.name || "Unknown"}
                </div>

                <div className={cn(
                  "p-4 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap",
                  isSelf 
                    ? "bg-primary text-primary-foreground rounded-tr-none" 
                    : "bg-white text-slate-800 border border-slate-100 rounded-tl-none"
                )}>
                  {msg.text_content}
                  <div className={cn(
                    "mt-2 text-[10px] opacity-70 text-right",
                    isSelf ? "text-primary-foreground" : "text-slate-400"
                  )}>
                    {new Date(msg.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
