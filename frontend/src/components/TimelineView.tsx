import React, { useEffect, useState } from 'react';
import api from '../services/api';
import type { EventSchema } from '../types/api';
import { Card } from './ui/card';
import { Skeleton } from './ui/skeleton';

const TimelineView: React.FC = () => {
  const [events, setEvents] = useState<EventSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/events/')
      .then(res => {
        // Defensive: log and check if array
        console.log('Events API response:', res.data);
        if (Array.isArray(res.data)) {
          setEvents(res.data);
        } else if (res.data && Array.isArray(res.data.results)) {
          setEvents(res.data.results);
        } else {
          setError('Unexpected API response format.');
        }
      })
      .catch(err => {
        setError('Failed to load events.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Skeleton className="h-40 w-full" />;
  }
  if (error) {
    return <div className="text-red-500">{error}</div>;
  }

  return (
    <div className="space-y-4">
      {events.map(event => (
        <Card key={event.id} className="p-4 shadow-md">
          <div className="text-xs text-gray-500">{new Date(event.date).toLocaleDateString()}</div>
          <div className="font-semibold text-lg">{event.explanation}</div>
          {event.email_quote && <div className="italic text-sm mt-2">"{event.email_quote}"</div>}
        </Card>
      ))}
    </div>
  );
};

export default TimelineView;
