import React, { useEffect, useState } from 'react';
import { documentService } from '../services/documentService';
import type { Document } from '@/types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText, TreePine, Trash2, Search, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Input } from '@/components/ui/input';

const DocumentLibrary: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await documentService.list();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const filteredDocs = documents.filter(doc => 
    doc.title.toLowerCase().includes(filter.toLowerCase())
  );

  const handleDelete = async (id: number) => {
    if (confirm('Permanently delete this document from archives?')) {
      try {
        await documentService.delete(id);
        fetchDocuments();
      } catch (error) {
        alert('Failed to delete document.');
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-in fade-in duration-500 font-sans">
      <div className="flex justify-between items-end">
        <div className="space-y-1">
          <h1 className="text-3xl font-black tracking-tighter text-slate-900 uppercase">Document Library</h1>
          <p className="text-slate-500 font-medium italic">Comprehensive archive of all scanned and digital filings.</p>
        </div>
        <Button className="font-bold bg-primary shadow-lg shadow-primary/20">
          <Plus className="h-4 w-4 mr-2" /> Index New Document
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      <Card className="shadow-xl border-slate-200 overflow-hidden">
        <CardHeader className="bg-slate-50/50 border-b pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-black uppercase tracking-widest text-slate-400">Archive Registry</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
              <Input 
                placeholder="Filter by title..." 
                className="pl-9 h-8 text-xs bg-white focus-visible:ring-1"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-slate-50/30">
              <TableRow>
                <TableHead className="font-black text-[10px] uppercase tracking-widest py-4 pl-6">Identifier & Title</TableHead>
                <TableHead className="font-black text-[10px] uppercase tracking-widest">Author</TableHead>
                <TableHead className="font-black text-[10px] uppercase tracking-widest text-center">Format</TableHead>
                <TableHead className="font-black text-[10px] uppercase tracking-widest">Filing Date</TableHead>
                <TableHead className="text-right font-black text-[10px] uppercase tracking-widest pr-6">Operations</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array(5).fill(0).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={5} className="py-4 px-6"><Skeleton className="h-6 w-full" /></TableCell>
                  </TableRow>
                ))
              ) : filteredDocs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-20 text-slate-400 font-bold uppercase text-xs tracking-widest">
                    No documents found matching criteria
                  </TableCell>
                </TableRow>
              ) : filteredDocs.map(doc => (
                <TableRow key={doc.id} className="hover:bg-slate-50/50 transition-colors group">
                  <TableCell className="py-4 pl-6">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 rounded-lg text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors border border-blue-100">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 group-hover:text-primary transition-colors">{doc.title}</p>
                        <p className="text-[10px] text-slate-400 font-black uppercase tracking-tighter">REF: DOC-{doc.id}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm font-bold text-slate-600 uppercase tracking-tighter">
                    {doc.author ? `${doc.author.first_name} ${doc.author.last_name}` : '--'}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={doc.source_type === 'REPRODUCED' ? 'secondary' : 'outline'} className="text-[9px] font-black tracking-widest px-2">
                      {doc.source_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-500 font-mono">
                    {doc.document_original_date || 'YYYY-MM-DD'}
                  </TableCell>
                  <TableCell className="text-right pr-6 space-x-1">
                    <Link to={`/documents/${doc.id}/tree`}>
                      <Button variant="ghost" size="sm" className="font-black text-[10px] uppercase tracking-widest text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                        <TreePine className="h-3.5 w-3.5 mr-1.5" /> View Tree
                      </Button>
                    </Link>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-red-400 hover:text-red-600 hover:bg-red-50"
                      onClick={() => handleDelete(doc.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentLibrary;
