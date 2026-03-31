import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { 
  ChevronLeft, 
  Calendar, 
  Mail, 
  Image as ImageIcon,
  Quote,
  Trash2,
  Edit,
  ExternalLink
} from 'lucide-react';
import { cn } from '../lib/utils';

interface Photo {
  id: number;
  file: string;
  file_name: string;
}

interface Email {
  id: number;
  subject: string;
  sender_email: string;
}

interface EventDetail {
  id: number;
  date: string;
  explanation: string;
  email_quote: string | null;
  linked_email: Email | null;
  linked_photos: Photo[];
  children: any[];
}

export default function EventDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(`/events/${eventId}/`)
      .then(res => {
        setEvent(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch event:', err);
        setError('Failed to load event details.');
        setLoading(false);
      });
  }, [eventId]);

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading event...</div>;
  if (error || !event) return <div className="p-8 text-center text-red-500">{error || 'Event not found.'}</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link 
          to="/events"
          className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), "text-slate-500 hover:text-slate-900")}
        >
          <ChevronLeft className="h-5 w-5 mr-1" /> Back to Timeline
        </Link>
        <div className="flex items-center gap-2">
           <Button variant="outline" size="sm" disabled>
             <Edit className="h-4 w-4 mr-2" /> Edit
           </Button>
           <Button variant="ghost" size="sm" className="text-red-500" disabled>
             <Trash2 className="h-4 w-4 mr-2" /> Delete
           </Button>
        </div>
      </div>

      <Card className="shadow-sm border-slate-200 overflow-hidden">
        <CardHeader className="bg-slate-50/50 border-b border-slate-100 py-6">
          <div className="flex items-center gap-3 text-primary mb-2">
            <Calendar className="h-5 w-5" />
            <span className="text-sm font-bold uppercase tracking-wider">{event.date}</span>
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900 leading-snug">
            {event.explanation || 'Untitled Event'}
          </CardTitle>
        </CardHeader>

        <CardContent className="p-8 space-y-8">
          {/* Linked Email / Quote */}
          {event.linked_email && (
            <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-6 relative overflow-hidden">
              <Quote className="absolute -top-2 -right-2 h-16 w-16 text-blue-100/50 -rotate-12" />
              <div className="relative">
                <div className="flex items-center gap-2 text-blue-700 font-semibold text-sm mb-4">
                  <Mail className="h-4 w-4" />
                  Linked Evidence: Email
                </div>
                
                <div className="space-y-4">
                  <div className="text-slate-700 italic text-lg leading-relaxed">
                    "{event.email_quote || 'No quote extracted.'}"
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-blue-100">
                    <div className="text-sm">
                      <span className="text-slate-500">From email:</span>{' '}
                      <span className="font-medium text-slate-800">{event.linked_email.subject}</span>
                    </div>
                    <Link 
                      to={`/emails/threads/${event.linked_email.id}`} // assuming simple routing for now
                      className={cn(buttonVariants({ variant: 'link', size: 'sm' }), "text-blue-600 p-0 h-auto")}
                    >
                      View Thread <ExternalLink className="h-3 w-3 ml-1" />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Photos */}
          {event.linked_photos.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <ImageIcon className="h-4 w-4" /> Supporting Photos
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {event.linked_photos.map(photo => (
                  <a 
                    key={photo.id} 
                    href={photo.file} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="group relative aspect-square bg-slate-100 rounded-lg overflow-hidden border border-slate-200"
                  >
                    <img 
                      src={photo.file} 
                      alt={photo.file_name}
                      className="w-full h-full object-cover transition-transform group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <ExternalLink className="text-white h-6 w-6" />
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Children / Sub-events can be added here if needed */}
        </CardContent>
      </Card>
    </div>
  );
}
