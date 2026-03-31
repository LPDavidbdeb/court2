import React, { useEffect, useState } from 'react';
import { pdfService } from '../services/pdfService';
import type { PDFDocument, PDFQuote } from '@/types/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FileText, Search, Quote, Download, Trash2, ArrowRight } from 'lucide-react';
import { Input } from '@/components/ui/input';

const PDFVault: React.FC = () => {
  const [pdfs, setPdfs] = useState<PDFDocument[]>([]);
  const [selectedPdf, setSelectedPdf] = useState<PDFDocument | null>(null);
  const [quotes, setQuotes] = useState<PDFQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [quotesLoading, setQuotesLoading] = useState(false);

  useEffect(() => {
    const fetchPdfs = async () => {
      try {
        setLoading(true);
        const data = await pdfService.list();
        setPdfs(data);
      } catch (error) {
        console.error('Error fetching PDFs:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchPdfs();
  }, []);

  const handleSelectPdf = async (pdf: PDFDocument) => {
    setSelectedPdf(pdf);
    try {
      setQuotesLoading(true);
      const data = await pdfService.getQuotes(pdf.id);
      setQuotes(data);
    } catch (error) {
      console.error('Error fetching PDF quotes:', error);
    } finally {
      setQuotesLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-black tracking-tighter text-slate-900">PDF Vault</h1>
        <p className="text-slate-500">Evidence archive for all scanned and digital PDF filings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* PDF List */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input placeholder="Filter PDFs..." className="pl-10 bg-white" />
          </div>
          
          <div className="space-y-2">
            {loading ? (
              Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-xl" />)
            ) : pdfs.map(pdf => (
              <Card 
                key={pdf.id} 
                className={`cursor-pointer transition-all hover:shadow-md ${selectedPdf?.id === pdf.id ? 'border-primary ring-1 ring-primary bg-primary/5' : 'bg-white'}`}
                onClick={() => handleSelectPdf(pdf)}
              >
                <CardHeader className="p-4 flex flex-row items-center gap-4 space-y-0">
                  <div className={`p-2 rounded-lg ${selectedPdf?.id === pdf.id ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'}`}>
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-sm font-bold truncate">{pdf.title}</CardTitle>
                    <CardDescription className="text-[10px] uppercase font-bold tracking-widest mt-1">
                      {pdf.author ? `${pdf.author.first_name[0]}. ${pdf.author.last_name}` : 'No Author'}
                    </CardDescription>
                  </div>
                  <ArrowRight className={`h-4 w-4 transition-transform ${selectedPdf?.id === pdf.id ? 'translate-x-1 opacity-100' : 'opacity-0'}`} />
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>

        {/* PDF Detail & Quotes */}
        <div className="lg:col-span-2 space-y-6">
          {selectedPdf ? (
            <>
              <Card className="border-none shadow-xl bg-slate-900 text-white overflow-hidden">
                <CardHeader className="pb-6">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <Badge variant="outline" className="text-white border-white/20 font-bold text-[10px] tracking-widest mb-2 uppercase">PDF Evidence</Badge>
                      <CardTitle className="text-3xl font-black tracking-tight">{selectedPdf.title}</CardTitle>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="bg-white/10 border-white/20 text-white hover:bg-white/20">
                        <Download className="h-4 w-4 mr-2" /> Source
                      </Button>
                      <Button variant="destructive" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="bg-white/5 border-t border-white/10 py-4 px-6 flex gap-8">
                   <div className="flex flex-col">
                     <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Document Date</span>
                     <span className="text-sm font-bold">{selectedPdf.document_date ? new Date(selectedPdf.document_date).toLocaleDateString() : 'N/A'}</span>
                   </div>
                   <div className="flex flex-col">
                     <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Author Profile</span>
                     <span className="text-sm font-bold">{selectedPdf.author ? `${selectedPdf.author.first_name} ${selectedPdf.author.last_name}` : 'Unknown'}</span>
                   </div>
                </CardContent>
              </Card>

              <div className="space-y-4">
                <div className="flex items-center gap-2 px-1">
                  <Quote className="h-5 w-5 text-primary" />
                  <h2 className="text-xl font-black tracking-tighter">Extracted Claims</h2>
                  <Badge variant="secondary" className="ml-auto font-bold">{quotes.length}</Badge>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {quotesLoading ? (
                    Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-32 w-full rounded-xl" />)
                  ) : quotes.length === 0 ? (
                    <div className="py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
                      <p className="text-slate-400 font-bold uppercase text-xs tracking-widest italic">No quotes extracted for this document</p>
                    </div>
                  ) : quotes.map(quote => (
                    <Card key={quote.id} className="border-l-4 border-l-blue-500 shadow-sm hover:shadow-md transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start mb-4">
                          <Badge variant="outline" className="font-bold text-[9px]">PAGE {quote.page_number}</Badge>
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">ID: Q-{quote.id}</span>
                        </div>
                        <p className="text-sm text-slate-700 leading-relaxed font-medium italic">
                          "{quote.quote_text}"
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="h-full flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50/50 py-20">
              <FileText className="h-16 w-16 text-slate-200 mb-4" />
              <p className="text-slate-400 font-black uppercase text-sm tracking-[0.2em]">Select an archive to analyze</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PDFVault;
