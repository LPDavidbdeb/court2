import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

interface Protagonist {
  id: number;
  first_name: string;
  last_name: string | null;
  role: string;
}

function fullName(p: Protagonist): string {
  return `${p.first_name} ${p.last_name ?? ''}`.trim();
}

export default function EmlUpload() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);

  const [protagonists, setProtagonists] = useState<Protagonist[]>([]);
  const [protagonistId, setProtagonistId] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/protagonists/')
      .then(res => setProtagonists(res.data))
      .catch(() => {/* non-blocking: dropdown stays empty */});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const file = fileRef.current?.files?.[0];
    if (!file) { setError('Please select a .eml file.'); return; }

    const formData = new FormData();
    formData.append('eml_file', file);
    if (protagonistId) formData.append('protagonist_id', protagonistId);

    setSubmitting(true);
    try {
      const res = await api.post('/emails/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.success) {
        navigate(`/emails/threads/${res.data.thread_id}`);
      } else {
        setError(res.data.message ?? 'Upload failed.');
      }
    } catch {
      setError('Upload failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl">
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between py-4">
          <CardTitle className="text-lg font-bold">Upload EML File</CardTitle>
          <Link to="/emails/threads">
            <Button size="sm" variant="secondary">Back to List</Button>
          </Link>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="pt-6 space-y-5">
            {/* EML file input */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                EML File <span className="text-red-500">*</span>
              </label>
              <input
                ref={fileRef}
                type="file"
                accept=".eml,message/rfc822"
                required
                className="block w-full text-sm text-slate-700 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-slate-300 file:bg-white file:text-sm file:text-slate-700 hover:file:bg-slate-50 cursor-pointer"
              />
              <p className="text-xs text-slate-400 mt-1">Select a single .eml file exported from your email client.</p>
            </div>

            {/* Protagonist dropdown */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Associated Protagonist <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <select
                value={protagonistId}
                onChange={e => setProtagonistId(e.target.value)}
                className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white"
              >
                <option value="">— None —</option>
                {protagonists.map(p => (
                  <option key={p.id} value={p.id}>
                    {fullName(p)} ({p.role})
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                {error}
              </p>
            )}
          </CardContent>

          <CardFooter className="border-t bg-slate-50/50 flex gap-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Uploading…' : 'Upload EML'}
            </Button>
            <Link to="/emails/threads">
              <Button type="button" variant="outline">Cancel</Button>
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
