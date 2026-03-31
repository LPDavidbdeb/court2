import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Eye, Plus, Trash2, Image as ImageIcon, Mail } from 'lucide-react';
import { cn } from '../lib/utils';

interface Event {
  id: number;
  date: string;
  explanation: string;
  photo_count: number;
  linked_email_id: number | null;
}

export default function EventsTimeline() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/events/')
      .then(res => {
        setEvents(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch events:', err);
        setError('Failed to load events.');
        setLoading(false);
      });
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this event?')) return;
    try {
      await api.delete(`/events/${id}/`);
      setEvents(events.filter(e => e.id !== id));
    } catch (err) {
      console.error('Failed to delete event:', err);
      alert('Failed to delete event.');
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading timeline...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Events Timeline</h1>
          <p className="text-slate-500">A chronological record of all case events.</p>
        </div>
        <Button disabled>
          <Plus className="h-4 w-4 mr-2" /> Add Event (soon)
        </Button>
      </div>

      <div className="relative border-l-2 border-slate-200 ml-4 pl-8 space-y-8">
        {events.length === 0 ? (
          <div className="text-slate-400 italic py-4">No events recorded.</div>
        ) : (
          events.map(event => (
            <div key={event.id} className="relative">
              {/* Timeline Dot */}
              <div className="absolute -left-[41px] top-1 w-5 h-5 rounded-full border-4 border-white bg-primary shadow-sm" />
              
              <div className="flex flex-col md:flex-row gap-4">
                <div className="shrink-0 w-32">
                  <div className="text-sm font-bold text-primary">{event.date}</div>
                </div>

                <Card className="flex-1 shadow-sm border-slate-200 hover:border-primary/30 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start gap-4">
                      <div className="space-y-3 flex-1">
                        <div className="text-slate-700 leading-relaxed">
                          {event.explanation || <span className="text-slate-400 italic">No explanation provided.</span>}
                        </div>
                        
                        <div className="flex flex-wrap gap-3">
                          {event.photo_count > 0 && (
                            <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded">
                              <ImageIcon className="h-3.5 w-3.5" />
                              {event.photo_count} photos
                            </div>
                          )}
                          {event.linked_email_id && (
                            <div className="flex items-center gap-1.5 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              <Mail className="h-3.5 w-3.5" />
                              Linked Email
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        <Link 
                          to={`/events/${event.id}`}
                          className={cn(buttonVariants({ variant: 'ghost', size: 'icon-sm' }), "text-slate-400 hover:text-primary")}
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                        <Button 
                          variant="ghost" 
                          size="icon-sm" 
                          className="text-slate-400 hover:text-red-500"
                          onClick={() => handleDelete(event.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
