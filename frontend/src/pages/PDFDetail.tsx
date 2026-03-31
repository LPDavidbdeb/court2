import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Button, buttonVariants } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  ChevronLeft, 
  ExternalLink, 
  Quote as QuoteIcon, 
  Trash2, 
  Plus, 
  Bot,
  Calendar,
  User,
  Info
} from 'lucide-react';
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

interface PDFQuote {
  id: number;
  quote_text: string;
  page_number: number;
  quote_location_details: string | null;
  created_at: string;
}

interface PDFDocument {
  id: number;
  title: string;
  author: Protagonist | null;
  document_date: string | null;
  document_type: PDFDocumentType | null;
  file: string;
  ai_analysis: string | null;
  uploaded_at: string;
  quotes: PDFQuote[];
}

export default function PDFDetail() {
  const { pdfId } = useParams<{ pdfId: string }>();
  const [pdf, setPdf] = useState<PDFDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Quote form state
  const [quoteText, setQuoteText] = useState('');
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [submitting, setSubmitting] = useState(false);

  const fetchPdf = () => {
    api.get(`/pdfs/${pdfId}/`)
      .then(res => {
        setPdf(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch PDF details:', err);
        setError('Failed to load PDF details.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPdf();
  }, [pdfId]);

  const handleCreateQuote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quoteText.trim()) return;

    setSubmitting(true);
    try {
      await api.post(`/pdfs/${pdfId}/quotes/`, {
        quote_text: quoteText,
        page_number: pageNumber
      });
      setQuoteText('');
      setPageNumber(1);
      fetchPdf(); // Refresh to show new quote
    } catch (err) {
      console.error('Failed to create quote:', err);
      alert('Failed to create quote.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteQuote = async (quoteId: number) => {
    if (!confirm('Are you sure you want to delete this quote?')) return;

    try {
      await api.delete(`/pdfs/quotes/${quoteId}/`);
      fetchPdf(); // Refresh
    } catch (err) {
      console.error('Failed to delete quote:', err);
      alert('Failed to delete quote.');
    }
  };

  if (loading) return <div className="p-8 text-center animate-pulse text-slate-500">Loading document...</div>;
  if (error || !pdf) return <div className="p-8 text-center text-red-500">{error || 'Document not found.'}</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div className="flex items-center gap-4">
          <Link 
            to="/pdfs"
            className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), "p-0 hover:bg-transparent text-slate-500 hover:text-slate-900")}
          >
            <ChevronLeft className="h-5 w-5 mr-1" /> Back to Vault
          </Link>
          <h1 className="text-xl font-bold text-slate-900 truncate max-w-[500px]">{pdf.title}</h1>
          <Badge variant="outline" className="bg-slate-50 text-slate-600 border-slate-200">
            {pdf.document_type?.name || 'Uncategorized'}
          </Badge>
        </div>
        <a 
          href={pdf.file} 
          target="_blank" 
          rel="noopener noreferrer"
          className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
        >
          <ExternalLink className="h-4 w-4 mr-2" /> Open Externally
        </a>
      </div>

      {/* Split Content */}
      <div className="flex flex-1 gap-6 min-h-0">
        {/* Left Side: PDF Viewer */}
        <div className="flex-1 bg-slate-100 rounded-lg border border-slate-200 overflow-hidden relative">
          <iframe 
            src={`${pdf.file}#toolbar=0`} 
            className="w-full h-full border-none"
            title={pdf.title}
          />
        </div>

        {/* Right Side: Details & Quotes */}
        <div className="w-96 flex flex-col gap-6 overflow-y-auto pr-2">
          {/* Metadata */}
          <Card className="shadow-sm border-slate-200 shrink-0">
            <CardHeader className="py-3 bg-slate-50/50 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Info className="h-4 w-4 text-primary" /> Document Info
              </CardTitle>
            </CardHeader>
            <CardContent className="py-3 space-y-2 text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <User className="h-4 w-4 text-slate-400" />
                <span className="font-medium">Author:</span> {pdf.author ? `${pdf.author.first_name} ${pdf.author.last_name || ''}` : 'N/A'}
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Calendar className="h-4 w-4 text-slate-400" />
                <span className="font-medium">Date:</span> {pdf.document_date || 'N/A'}
              </div>
            </CardContent>
          </Card>

          {/* AI Analysis */}
          <Card className="shadow-sm border-slate-200 shrink-0">
            <CardHeader className="py-3 bg-slate-50/50 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Bot className="h-4 w-4 text-indigo-500" /> AI Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="py-3">
              <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                {pdf.ai_analysis || <span className="text-slate-400 italic">No AI analysis available for this document.</span>}
              </div>
            </CardContent>
          </Card>

          {/* Quotes Section */}
          <div className="flex flex-col gap-4 flex-1">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                <QuoteIcon className="h-4 w-4 text-amber-500" /> Citations & Quotes
              </h2>
              <Badge variant="secondary" className="bg-amber-50 text-amber-600 border-none">
                {pdf.quotes.length}
              </Badge>
            </div>

            {/* Create Quote Form */}
            <form onSubmit={handleCreateQuote} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm space-y-3 shrink-0">
              <textarea
                placeholder="Extract text from PDF..."
                value={quoteText}
                onChange={(e) => setQuoteText(e.target.value)}
                className="w-full text-sm p-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary h-24 resize-none"
                required
              />
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Page:</span>
                <input
                  type="number"
                  min="1"
                  value={pageNumber}
                  onChange={(e) => setPageNumber(parseInt(e.target.value) || 1)}
                  className="w-16 text-xs p-1.5 border border-slate-200 rounded-md"
                />
                <Button type="submit" size="sm" className="ml-auto" disabled={submitting || !quoteText.trim()}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add Quote
                </Button>
              </div>
            </form>

            {/* Quotes List */}
            <div className="space-y-3">
              {pdf.quotes.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs italic border-2 border-dashed border-slate-100 rounded-lg">
                  No quotes extracted yet.
                </div>
              ) : (
                pdf.quotes.map(quote => (
                  <div key={quote.id} className="group relative bg-amber-50/50 p-3 rounded-lg border border-amber-100 transition-colors hover:bg-amber-50">
                    <button 
                      onClick={() => handleDeleteQuote(quote.id)}
                      className="absolute top-2 right-2 text-slate-300 hover:text-red-500 transition-opacity opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    <div className="text-sm text-slate-800 italic leading-snug pr-4">
                      "{quote.quote_text}"
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] font-bold text-amber-600 uppercase tracking-wider">
                      <span>Page {quote.page_number}</span>
                      <span className="text-slate-400 font-normal">{new Date(quote.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
