import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { FileText, Plus, ExternalLink, Eye, Trash2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface Protagonist {
  id: number;
  first_name: string;
  last_name: string | null;
}

interface PDFDocumentType {
  id: number;
  name: string;
}

interface PDFDocument {
  id: number;
  title: string;
  author: Protagonist | null;
  document_date: string | null;
  document_type: PDFDocumentType | null;
  file: string;
  uploaded_at: string;
}

export default function PDFVault() {
  const [pdfs, setPdfs] = useState<PDFDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get('/pdfs/')
      .then(res => {
        setPdfs(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch PDFs:', err);
        setError('Failed to load PDF documents.');
        setLoading(false);
      });
  }, []);

  const groupedPdfs = useMemo(() => {
    const groups: Record<string, PDFDocument[]> = {};
    pdfs.forEach(pdf => {
      const typeName = pdf.document_type?.name || 'Uncategorized';
      if (!groups[typeName]) groups[typeName] = [];
      groups[typeName].push(pdf);
    });
    return groups;
  }, [pdfs]);

  const [activeTab, setActiveTab] = useState<string>('');

  useEffect(() => {
    const types = Object.keys(groupedPdfs);
    if (types.length > 0 && !activeTab) {
      setActiveTab(types[0]);
    }
  }, [groupedPdfs, activeTab]);

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading PDF Vault...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">PDF Vault</h1>
          <p className="text-slate-500">Manage and explore all PDF evidence.</p>
        </div>
        <Button disabled>
          <Plus className="h-4 w-4 mr-2" /> Upload PDF (soon)
        </Button>
      </div>

      <Card className="shadow-sm border-slate-200">
        <CardHeader className="bg-slate-50/50 border-b border-slate-100">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Documents
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {pdfs.length === 0 ? (
            <div className="p-12 text-center text-slate-400">
              No PDF documents found.
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="flex border-b border-slate-100 bg-slate-50/30 overflow-x-auto">
                {Object.keys(groupedPdfs).sort().map(typeName => (
                  <button
                    key={typeName}
                    onClick={() => setActiveTab(typeName)}
                    className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 
                      ${activeTab === typeName 
                        ? 'border-primary text-primary bg-white' 
                        : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                      }`}
                  >
                    {typeName}
                    <Badge variant="secondary" className="ml-2 bg-slate-100 text-slate-500 border-none">
                      {groupedPdfs[typeName].length}
                    </Badge>
                  </button>
                ))}
              </div>

              {/* Document List */}
              <div className="divide-y divide-slate-100">
                {activeTab && groupedPdfs[activeTab]?.map(pdf => (
                  <div key={pdf.id} className="p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-slate-50/50 transition-colors">
                    <div className="min-w-0 flex-1">
                      <Link 
                        to={`/pdfs/${pdf.id}`}
                        className="text-base font-semibold text-slate-900 hover:text-primary transition-colors block truncate"
                      >
                        {pdf.title}
                      </Link>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs text-slate-500">
                        <span>Date: {pdf.document_date || 'N/A'}</span>
                        <span>Author: {pdf.author ? `${pdf.author.first_name} ${pdf.author.last_name || ''}` : 'N/A'}</span>
                        <span>Uploaded: {new Date(pdf.uploaded_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <a 
                        href={pdf.file} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" /> Open
                      </a>
                      <Link 
                        to={`/pdfs/${pdf.id}`}
                        className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                      >
                        <Eye className="h-4 w-4 mr-2" /> Details
                      </Link>
                      <Button variant="ghost" size="sm" className="text-slate-400 hover:text-red-500" disabled>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
