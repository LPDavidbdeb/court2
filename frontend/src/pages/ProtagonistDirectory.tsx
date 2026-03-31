import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

interface ContactEmail {
  id: number;
  email_address: string;
  description: string | null;
}

interface ProtagonistListItem {
  id: number;
  first_name: string;
  last_name: string | null;
  role: string;
  linkedin_url: string | null;
  emails: ContactEmail[];
  email_thread_count: number;
  photo_document_count: number;
}

function fullName(p: ProtagonistListItem): string {
  return `${p.first_name} ${p.last_name ?? ''}`.trim();
}

export default function ProtagonistDirectory() {
  const [protagonists, setProtagonists] = useState<ProtagonistListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  useEffect(() => {
    api.get('/protagonists/')
      .then(res => setProtagonists(res.data))
      .catch(() => setError('Failed to load protagonists.'))
      .finally(() => setLoading(false));
  }, []);

  // Unique roles for the filter dropdown
  const roles = useMemo(
    () => Array.from(new Set(protagonists.map(p => p.role))).sort(),
    [protagonists]
  );

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return protagonists.filter(p => {
      const matchesSearch = !q || fullName(p).toLowerCase().includes(q) ||
        p.role.toLowerCase().includes(q);
      const matchesRole = !roleFilter || p.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [protagonists, search, roleFilter]);

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="max-w-6xl">
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between py-4">
          <CardTitle className="text-lg font-bold">
            Protagonist Directory
            <span className="ml-2 text-sm font-normal opacity-80">
              ({protagonists.length} {protagonists.length === 1 ? 'person' : 'people'})
            </span>
          </CardTitle>
        </CardHeader>

        {/* Search + filter toolbar */}
        <div className="flex flex-wrap gap-3 px-4 py-3 border-b border-slate-100 bg-slate-50/50">
          <input
            type="text"
            placeholder="Search by name or role…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 min-w-[200px] border border-slate-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          <select
            value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)}
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All roles</option>
            {roles.map(r => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          {(search || roleFilter) && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => { setSearch(''); setRoleFilter(''); }}
            >
              Clear
            </Button>
          )}
        </div>

        <CardContent className="p-0">
          {filtered.length === 0 ? (
            <div className="p-6 text-slate-500">
              {protagonists.length === 0
                ? 'No protagonists found.'
                : 'No results match your search.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200">
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Name</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Role</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Contact Emails</th>
                    <th className="text-center px-4 py-3 font-semibold text-slate-700">Email Threads</th>
                    <th className="text-center px-4 py-3 font-semibold text-slate-700">Photo Docs</th>
                    <th className="text-left px-4 py-3 font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((p, i) => (
                    <tr
                      key={p.id}
                      className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}
                    >
                      <td className="px-4 py-3 font-medium text-slate-900">
                        <Link
                          to={`/protagonists/${p.id}`}
                          className="text-primary hover:underline"
                        >
                          {fullName(p)}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{p.role}</td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {p.emails.length === 0 ? (
                          <span className="text-slate-300">—</span>
                        ) : (
                          <div className="space-y-0.5">
                            {p.emails.map(e => (
                              <div key={e.id}>
                                <span className="font-mono">{e.email_address}</span>
                                {e.description && (
                                  <span className="text-slate-400 ml-1">({e.description})</span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {p.email_thread_count > 0 ? (
                          <span className="inline-block bg-sky-100 text-sky-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                            {p.email_thread_count}
                          </span>
                        ) : (
                          <span className="text-slate-300">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {p.photo_document_count > 0 ? (
                          <span className="inline-block bg-violet-100 text-violet-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                            {p.photo_document_count}
                          </span>
                        ) : (
                          <span className="text-slate-300">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Link to={`/protagonists/${p.id}`}>
                          <Button size="sm" variant="outline" className="text-sky-600 border-sky-300 hover:bg-sky-50">
                            View
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
