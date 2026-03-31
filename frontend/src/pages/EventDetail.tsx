import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Calendar, FileText, MessageSquare, Image as ImageIcon, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Photo {
  id: number;
  title?: string;
  file?: string;
}

interface EventDetail {
  id: number;
  date: string;
  explanation: string;
  email_quote?: string;
  linked_email_id?: number;
  linked_photos: Photo[];
  children: any[];
}

const EventDetailView: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEventDetail = async () => {
      try {
        const response = await api.get(`/events/${eventId}`);
        setEvent(response.data);
      } catch (err) {
        console.error("Failed to fetch event details", err);
      } finally {
        setLoading(false);
      }
    };
    if (eventId) fetchEventDetail();
  }, [eventId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-[200px]" />
        <Skeleton className="h-[300px] w-full" />
        <Skeleton className="h-[200px] w-full" />
      </div>
    );
  }

  if (!event) return <div className="text-center py-20">Event not found.</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/events')} className="group">
          <ArrowLeft className="mr-2 h-4 w-4 group-hover:-translate-x-1 transition-transform" /> 
          Back to Timeline
        </Button>
        <Badge variant="outline" className="font-mono">ID: E-{event.id}</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-t-4 border-t-primary shadow-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <Calendar className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {new Date(event.date).toLocaleDateString('fr-CA', { 
                    weekday: 'long',
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </span>
              </div>
              <CardTitle className="text-2xl leading-tight">Event Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 leading-relaxed text-lg italic whitespace-pre-wrap">
                  {event.explanation || 'No detailed explanation provided for this event.'}
                </p>
              </div>
            </CardContent>
          </Card>

          {event.email_quote && (
            <Card className="bg-blue-50/30 border-blue-100">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-blue-600">
                  <MessageSquare className="h-4 w-4" />
                  <CardTitle className="text-sm uppercase tracking-wider">Linked Email Excerpt</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <blockquote className="border-l-4 border-blue-200 pl-4 py-1 italic text-slate-700 font-sans leading-relaxed">
                  {event.email_quote}
                </blockquote>
                {event.linked_email_id && (
                  <Link to={`/emails/threads`}>
                    <Button variant="link" size="sm" className="p-0 h-auto mt-4 text-blue-600 font-bold">
                      View Source Email Thread <ChevronRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar / Attachments */}
        <div className="space-y-6">
          <Card className="shadow-sm">
            <CardHeader className="pb-3 bg-slate-50/50 border-b">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-slate-500" />
                <CardTitle className="text-sm font-bold uppercase">Linked Photos</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {event.linked_photos.length === 0 ? (
                <p className="text-sm text-slate-400 italic">No photos attached.</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {event.linked_photos.map(photo => (
                    <div key={photo.id} className="aspect-square bg-slate-100 rounded-md overflow-hidden border border-slate-200 group relative">
                      {photo.file ? (
                        <img 
                          src={photo.file} 
                          alt={photo.title || "Evidence"} 
                          className="w-full h-full object-cover transition-transform group-hover:scale-110"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-300">
                          <ImageIcon className="h-8 w-8" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {event.children && event.children.length > 0 && (
            <Card className="shadow-sm">
              <CardHeader className="pb-3 bg-slate-50/50 border-b">
                <CardTitle className="text-sm font-bold uppercase">Sub-Events</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-2">
                {event.children.map(child => (
                  <Link key={child.id} to={`/events/${child.id}`} className="block p-2 rounded hover:bg-slate-100 text-sm transition-colors border border-transparent hover:border-slate-200">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{new Date(child.date).toLocaleDateString()}</span>
                      <ChevronRight className="h-3 w-3 text-slate-400" />
                    </div>
                    <p className="text-xs text-slate-500 truncate mt-1">{child.explanation}</p>
                  </Link>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventDetailView;
