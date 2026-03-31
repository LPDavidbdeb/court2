import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { CalendarDays, ExternalLink, MessageSquare, Image as ImageIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Event {
  id: number;
  date: string;
  explanation: string;
  email_quote?: string;
  linked_email_id?: number;
}

const EventsView: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await api.get('/events/');
        setEvents(response.data);
      } catch (err) {
        console.error("Failed to fetch events", err);
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-[250px]" />
        <Card>
          <CardContent className="pt-6">
            <Skeleton className="h-[500px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Events Timeline</h1>
          <p className="text-slate-500 text-sm">Chronological registry of all supporting evidence and occurrences.</p>
        </div>
        <Button className="font-bold">
          Add New Event
        </Button>
      </div>

      <Card className="shadow-sm border-slate-200">
        <CardHeader className="bg-slate-50/50 border-b">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Event Registry</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-slate-50/30">
              <TableRow>
                <TableHead className="w-[150px] font-bold">Date</TableHead>
                <TableHead className="font-bold">Explanation / Description</TableHead>
                <TableHead className="w-[120px] font-bold">Evidence</TableHead>
                <TableHead className="text-right font-bold">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-12 text-muted-foreground italic">
                    No events registered in the timeline.
                  </TableCell>
                </TableRow>
              ) : (
                events.map((event) => (
                  <TableRow key={event.id} className="hover:bg-slate-50/50 transition-colors group">
                    <TableCell className="font-mono text-sm align-top pt-4">
                      {new Date(event.date).toLocaleDateString('fr-CA', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </TableCell>
                    <TableCell className="align-top pt-4">
                      <div className="space-y-2">
                        <p className="text-sm text-slate-700 leading-relaxed line-clamp-2 group-hover:line-clamp-none transition-all">
                          {event.explanation || '(No explanation provided)'}
                        </p>
                        {event.email_quote && (
                          <div className="bg-blue-50/50 border-l-2 border-blue-200 p-2 rounded-r-md">
                            <p className="text-xs italic text-blue-700">
                              <MessageSquare className="h-3 w-3 inline mr-1 opacity-70" />
                              "{event.email_quote.substring(0, 100)}..."
                            </p>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="align-top pt-4">
                      <div className="flex gap-1">
                        {event.linked_email_id && (
                          <Badge variant="secondary" className="bg-blue-100 text-blue-700 hover:bg-blue-200 border-none cursor-default">
                            Email
                          </Badge>
                        )}
                        {/* Logic for photos would go here once related_name or endpoint is confirmed */}
                      </div>
                    </TableCell>
                    <TableCell className="text-right align-top pt-3">
                      <Link to={`/events/${event.id}`}>
                        <Button variant="ghost" size="sm" className="hover:bg-white hover:shadow-sm border border-transparent hover:border-slate-200">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Details
                        </Button>
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

export default EventsView;
