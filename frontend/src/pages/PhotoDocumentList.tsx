import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';

interface PhotoDocumentListItem {
  id: number;
  title: string;
  description: string | null;
  photo_count: number;
  created_at: string;
}

export default function PhotoDocumentList() {
  const [documents, setDocuments] = useState<PhotoDocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/photos/documents/')
      .then(res => setDocuments(res.data))
      .catch(() => setError('Failed to load documents.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error) return <div className="p-8 text-red-600">{error}</div>;

  return (
    <div className="max-w-6xl">
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground flex flex-row items-center justify-between">
          <CardTitle className="text-lg font-bold">Photo Documents</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {documents.length === 0 ? (
            <div className="p-6 text-slate-500">No photo documents have been created yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-800 text-white">
                    <th className="text-left px-4 py-3 font-semibold">Title</th>
                    <th className="text-left px-4 py-3 font-semibold">Description</th>
                    <th className="text-left px-4 py-3 font-semibold">Photo Count</th>
                    <th className="text-left px-4 py-3 font-semibold">Created</th>
                    <th className="text-left px-4 py-3 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc, i) => (
                    <tr key={doc.id} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                      <td className="px-4 py-3">
                        <Link
                          to={`/photos/documents/${doc.id}`}
                          className="text-primary font-medium hover:underline"
                        >
                          {doc.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-slate-600 max-w-xs truncate">
                        {doc.description
                          ? doc.description.replace(/<[^>]*>/g, '').slice(0, 100)
                          : <span className="text-slate-400 italic">No description</span>}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{doc.photo_count}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <Link to={`/photos/documents/${doc.id}`}>
                          <Button size="sm" variant="outline">View</Button>
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
