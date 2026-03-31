import { useEffect, useState, useRef, useCallback } from 'react';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { MessageSquare, Loader2, User, ChevronLeft } from 'lucide-react';
import { cn } from '../lib/utils';
import { Link } from 'react-router-dom';

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

const SELF_NAME = "Louis Philippe David";

export default function ChatStreamView() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const observer = useRef<IntersectionObserver | null>(null);

  const lastMessageRef = useCallback((node: HTMLDivElement | null) => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  useEffect(() => {
    setLoading(true);
    api.get(`/chats/messages/?page=${page}&page_size=50`)
      .then(res => {
        const newMessages = res.data;
        if (newMessages.length === 0) {
          setHasMore(false);
        } else {
          setMessages(prev => [...prev, ...newMessages]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch messages:', err);
        setLoading(false);
      });
  }, [page]);

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleString([], { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto border border-slate-200 rounded-xl overflow-hidden bg-slate-50 shadow-sm">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 p-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg">
            <MessageSquare className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900">Conversation Stream</h1>
            <p className="text-xs text-slate-500">Google Chat history</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" size="sm" asChild>
             <Link to="/chats/sequences">Manage Sequences</Link>
           </Button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, index) => {
          const isSelf = msg.sender?.name === SELF_NAME;
          const isLast = index === messages.length - 1;

          return (
            <div 
              key={msg.id} 
              ref={isLast ? lastMessageRef : null}
              className={cn(
                "flex flex-col max-w-[80%]",
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
                  {formatTimestamp(msg.timestamp)}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-center py-4">
            <Loader2 className="h-6 w-6 text-primary animate-spin" />
          </div>
        )}

        {!hasMore && messages.length > 0 && (
          <div className="text-center py-8 text-slate-400 text-xs font-medium uppercase tracking-widest">
            End of conversation
          </div>
        )}

        {!loading && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-400 space-y-2">
            <MessageSquare className="h-12 w-12 opacity-20" />
            <p>No messages found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
