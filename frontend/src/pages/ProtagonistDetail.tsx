import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

// ── Types ──────────────────────────────────────────────────────────────────────

interface ContactEmail {
  id: number;
  email_address: string;
  description: string | null;
}

interface EmailThreadSummary {
  id: number;
  subject: string | null;
  updated_at: string;
}

interface PhotoDocumentSummary {
  id: number;
  title: string;
  created_at: string;
}

interface ProtagonistDetail {
  id: number;
  first_name: string;
  last_name: string | null;
  role: string;
  linkedin_url: string | null;
  created_at: string;
  updated_at: string;
  emails: ContactEmail[];
  email_thread_count: number;
  photo_document_count: number;
  email_threads: EmailThreadSummary[];
  authored_photo_documents: PhotoDocumentSummary[];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return 'N/A';
  return new Date(iso).toLocaleString('fr-CA', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Evidence section card ─────────────────────────────────────────────────────

function EvidenceSection({
  title,
  badge,
  badgeColor,
  children,
}: {
  title: string;
  badge: number;
  badgeColor: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="bg-slate-600 text-white py-3 flex flex-row items-center gap-3">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${badgeColor}`}>
          {badge}
        </span>
      </CardHeader>
      <CardContent className="p-0">{children}</CardContent>
    </Card>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ProtagonistDetailPage() {
  const { protagonistId } = useParams<{ protagonistId: string }>();
  const [protagonist, setProtagonist] = useState<ProtagonistDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/protagonists/${protagonistId}/`)
      .then(res => setProtagonist(res.data))
      .catch(() => setError('Failed to load protagonist.'))
      .finally(() => setLoading(false));
  }, [protagonistId]);

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error || !protagonist) return <div className="p-8 text-red-600">{error || 'Not found.'}</div>;

  const fullName = `${protagonist.first_name} ${protagonist.last_name ?? ''}`.trim();

  return (
    <div className="max-w-4xl space-y-4">

      {/* ── Profile card ── */}
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between py-4">
          <CardTitle className="text-lg font-bold">{fullName}</CardTitle>
          <Link to="/protagonists">
            <Button size="sm" variant="secondary">Back to Directory</Button>
          </Link>
        </CardHeader>

        <CardContent className="pt-5 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="font-semibold text-slate-700">Role:</span>{' '}
              <span className="text-slate-600">{protagonist.role}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-700">LinkedIn:</span>{' '}
              {protagonist.linkedin_url ? (
                <a
                  href={protagonist.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline break-all"
                >
                  {protagonist.linkedin_url}
                </a>
              ) : (
                <span className="text-slate-400">—</span>
              )}
            </div>
            <div>
              <span className="font-semibold text-slate-700">Added:</span>{' '}
              <span className="text-slate-500">{formatDate(protagonist.created_at)}</span>
            </div>
            <div>
              <span className="font-semibold text-slate-700">Updated:</span>{' '}
              <span className="text-slate-500">{formatDate(protagonist.updated_at)}</span>
            </div>
          </div>

          {/* Contact emails */}
          {protagonist.emails.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <p className="text-sm font-semibold text-slate-700 mb-1">Known email addresses:</p>
              <ul className="space-y-1">
                {protagonist.emails.map(e => (
                  <li key={e.id} className="text-sm">
                    <span className="font-mono text-slate-700">{e.email_address}</span>
                    {e.description && (
                      <span className="text-slate-400 ml-2 text-xs">({e.description})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Linked email threads ── */}
      <EvidenceSection
        title="Linked Email Threads"
        badge={protagonist.email_thread_count}
        badgeColor="bg-sky-200 text-sky-800"
      >
        {protagonist.email_threads.length === 0 ? (
          <p className="px-4 py-4 text-sm text-slate-400">No email threads linked to this protagonist.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="text-left px-4 py-2 font-semibold text-slate-600">Subject</th>
                <th className="text-left px-4 py-2 font-semibold text-slate-600">Last Updated</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {protagonist.email_threads.map((t, i) => (
                <tr
                  key={t.id}
                  className={`border-b border-slate-100 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}
                >
                  <td className="px-4 py-2 text-slate-700 max-w-sm truncate">
                    {t.subject ?? '(No Subject)'}
                  </td>
                  <td className="px-4 py-2 text-slate-500 whitespace-nowrap text-xs">
                    {formatDate(t.updated_at)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link to={`/emails/threads/${t.id}`}>
                      <Button size="sm" variant="outline" className="text-sky-600 border-sky-300 hover:bg-sky-50">
                        View
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </EvidenceSection>

      {/* ── Authored photo documents ── */}
      <EvidenceSection
        title="Authored Photo Documents"
        badge={protagonist.photo_document_count}
        badgeColor="bg-violet-200 text-violet-800"
      >
        {protagonist.authored_photo_documents.length === 0 ? (
          <p className="px-4 py-4 text-sm text-slate-400">No photo documents authored by this protagonist.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="text-left px-4 py-2 font-semibold text-slate-600">Title</th>
                <th className="text-left px-4 py-2 font-semibold text-slate-600">Created</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {protagonist.authored_photo_documents.map((doc, i) => (
                <tr
                  key={doc.id}
                  className={`border-b border-slate-100 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}
                >
                  <td className="px-4 py-2 text-slate-700 max-w-sm truncate">{doc.title}</td>
                  <td className="px-4 py-2 text-slate-500 whitespace-nowrap text-xs">
                    {formatDate(doc.created_at)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <Link to={`/photos/documents/${doc.id}`}>
                      <Button size="sm" variant="outline" className="text-violet-600 border-violet-300 hover:bg-violet-50">
                        View
                      </Button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </EvidenceSection>

    </div>
  );
}
