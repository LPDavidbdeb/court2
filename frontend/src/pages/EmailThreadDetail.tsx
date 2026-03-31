import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

interface ProtagonistSummary {
  id: number;
  first_name: string;
  last_name: string | null;
  role: string;
}

interface EmailItem {
  id: number;
  subject: string | null;
  sender: string | null;
  recipients_to: string | null;
  recipients_cc: string | null;
  date_sent: string | null;
  body_plain_text: string | null;
  sender_protagonist: ProtagonistSummary | null;
}

interface EmailThreadDetail {
  id: number;
  thread_id: string;
  subject: string | null;
  saved_at: string;
  updated_at: string;
  protagonist: ProtagonistSummary | null;
  emails: EmailItem[];
}

function fullName(p: ProtagonistSummary | null): string {
  if (!p) return 'N/A';
  return `${p.first_name} ${p.last_name ?? ''}`.trim() || 'N/A';
}

function formatDate(iso: string | null): string {
  if (!iso) return 'N/A';
  return new Date(iso).toLocaleString('fr-CA', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Accordion email row ───────────────────────────────────────────────────────

interface EmailAccordionItemProps {
  email: EmailItem;
  defaultOpen: boolean;
}

function EmailAccordionItem({ email, defaultOpen }: EmailAccordionItemProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-slate-200 rounded-md overflow-hidden">
      {/* Header — always visible, mirrors accordion-button in detail.html */}
      <button
        className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-white hover:bg-slate-50 text-left transition-colors"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className="flex-1 text-sm">
          <strong className="text-slate-900">
            {email.subject ?? '(No Subject)'}
          </strong>
          <span className="text-slate-500 ml-2">— From: {email.sender ?? 'N/A'}</span>
          <span className="text-slate-400 text-xs ml-2">
            on {formatDate(email.date_sent)}
          </span>
        </span>
        <svg
          className={`h-4 w-4 text-slate-400 flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Body — collapsible, mirrors accordion-collapse in detail.html */}
      {open && (
        <div className="px-4 pb-4 pt-2 bg-white border-t border-slate-100">
          <p className="text-sm text-slate-700 mb-1">
            <strong>To:</strong> {email.recipients_to ?? 'N/A'}
          </p>
          {email.recipients_cc && (
            <p className="text-sm text-slate-700 mb-1">
              <strong>Cc:</strong> {email.recipients_cc}
            </p>
          )}
          <hr className="my-2 border-slate-100" />
          {/* email-body-scrollable — max 400 px, pre-wrap, monospace */}
          <div className="max-h-96 overflow-y-auto border border-slate-200 rounded p-3 bg-slate-50">
            <pre className="text-xs font-mono leading-relaxed whitespace-pre-wrap break-words">
              {email.body_plain_text ?? '(No body content available)'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function EmailThreadDetail() {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const [thread, setThread] = useState<EmailThreadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/emails/threads/${threadId}/`)
      .then(res => setThread(res.data))
      .catch(() => setError('Failed to load thread.'))
      .finally(() => setLoading(false));
  }, [threadId]);

  const handleDelete = async () => {
    if (!thread) return;
    if (!confirm('Are you sure you want to delete this entire thread? This action cannot be undone.')) return;
    try {
      await api.delete(`/emails/threads/${thread.id}/`);
      navigate('/emails/threads');
    } catch {
      alert('Failed to delete thread.');
    }
  };

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error || !thread) return <div className="p-8 text-red-600">{error || 'Thread not found.'}</div>;

  return (
    <div className="max-w-4xl space-y-4">

      {/* ── Thread metadata card ── */}
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between py-4">
          <CardTitle className="text-lg font-bold">Thread Details</CardTitle>
          <div className="flex gap-2">
            <Link to="/emails/threads">
              <Button size="sm" variant="secondary">Back to List</Button>
            </Link>
          </div>
        </CardHeader>

        <CardContent className="pt-4 space-y-2">
          <h2 className="text-base font-semibold text-slate-900">
            {thread.subject ?? '(No Subject)'}
          </h2>
          <p className="text-sm text-slate-700">
            <strong>Associated Protagonist:</strong> {fullName(thread.protagonist)}
          </p>
          <p className="text-sm text-slate-700">
            <strong>Thread ID:</strong>{' '}
            <span className="inline-block bg-slate-100 text-slate-600 text-xs font-mono px-2 py-0.5 rounded">
              {thread.thread_id}
            </span>
          </p>
          <p className="text-sm text-slate-700">
            <strong>Saved At:</strong> {formatDate(thread.saved_at)}
          </p>
          <p className="text-sm text-slate-700">
            <strong>Last Updated:</strong> {formatDate(thread.updated_at)}
          </p>
        </CardContent>

        <CardFooter className="border-t bg-slate-50/50">
          <Button
            variant="outline"
            size="sm"
            className="text-red-600 border-red-300 hover:bg-red-50"
            onClick={handleDelete}
          >
            Delete Thread
          </Button>
        </CardFooter>
      </Card>

      {/* ── Full conversation accordion ── */}
      {thread.emails.length > 0 && (
        <Card className="shadow-sm">
          <CardHeader className="bg-slate-600 text-white py-3">
            <CardTitle className="text-base font-semibold">
              Full Email Conversation ({thread.emails.length} message{thread.emails.length !== 1 ? 's' : ''})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {thread.emails.map((email, i) => (
              <EmailAccordionItem
                key={email.id}
                email={email}
                defaultOpen={i === 0}   // First message open by default — mirrors {% if forloop.first %}show{% endif %}
              />
            ))}
          </CardContent>
        </Card>
      )}

    </div>
  );
}
