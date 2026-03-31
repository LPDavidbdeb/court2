import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { caseService } from '../services/caseService';
import { LegalCaseDetail, PerjuryContestation, ProducedExhibit } from '../types/api';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, List as TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Briefcase, 
  Scale, 
  FileStack, 
  ArrowLeft, 
  Calendar,
  MessageSquare,
  AlertTriangle,
  History
} from 'lucide-react';

const CaseDashboard: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<LegalCaseDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCaseData = async () => {
      if (!caseId) return;
      try {
        setLoading(true);
        const data = await caseService.get(parseInt(caseId));
        setCaseData(data);
      } catch (error) {
        console.error('Error fetching case details:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCaseData();
  }, [caseId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-1/3" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!caseData) return <div className="text-center py-20 text-xl font-bold">Case not found.</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-black tracking-tighter text-slate-900">{caseData.title}</h1>
            <div className="flex items-center gap-2 text-slate-500 text-sm font-medium mt-1">
              <Calendar className="h-3 w-3" />
              <span>Registered on {new Date(caseData.created_at).toLocaleDateString()}</span>
              <span className="mx-1">•</span>
              <span className="font-bold text-primary uppercase text-[10px] tracking-widest">Case L-{caseData.id}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="font-bold">Generate Word Report</Button>
          <Button className="font-bold bg-primary text-primary-foreground shadow-lg shadow-primary/20">Recalculate Registry</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-slate-900 text-white border-none shadow-xl">
          <CardHeader className="pb-2">
            <CardDescription className="text-slate-400 font-bold uppercase text-[10px] tracking-widest">Total Exhibits</CardDescription>
            <CardTitle className="text-4xl font-black">{caseData.produced_exhibits.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 w-3/4" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-orange-500 text-white border-none shadow-xl">
          <CardHeader className="pb-2">
            <CardDescription className="text-orange-100 font-bold uppercase text-[10px] tracking-widest">Active Contestations</CardDescription>
            <CardTitle className="text-4xl font-black">{caseData.contestations.length}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-1 bg-orange-600 rounded-full overflow-hidden">
              <div className="h-full bg-white w-1/2" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white border-2 border-slate-100 shadow-xl">
          <CardHeader className="pb-2">
            <CardDescription className="text-slate-400 font-bold uppercase text-[10px] tracking-widest">Last Update</CardDescription>
            <CardTitle className="text-xl font-bold text-slate-900">
              {caseData.contestations.length > 0 
                ? new Date(caseData.contestations[0].updated_at).toLocaleDateString()
                : 'No activity'}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-2 text-slate-500 text-xs">
            <History className="h-3 w-3" />
            <span>Activity monitoring active</span>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="registry" className="w-full">
        <div className="flex items-center justify-between mb-4 border-b">
          <div className="flex gap-8">
            <TabsTrigger value="registry" className="pb-4 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent font-bold uppercase text-[11px] tracking-widest px-0">
              <FileStack className="h-4 w-4 mr-2" />
              Exhibit Registry
            </TabsTrigger>
            <TabsTrigger value="contestations" className="pb-4 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent font-bold uppercase text-[11px] tracking-widest px-0">
              <Scale className="h-4 w-4 mr-2" />
              Perjury Analysis
            </TabsTrigger>
          </div>
        </div>

        <TabsContent value="registry" className="mt-0">
          <Card className="shadow-sm border-slate-200">
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-slate-50/50">
                  <TableRow>
                    <TableHead className="w-[100px] font-black uppercase text-[10px]">Cote</TableHead>
                    <TableHead className="w-[150px] font-black uppercase text-[10px]">Type</TableHead>
                    <TableHead className="w-[150px] font-black uppercase text-[10px]">Date</TableHead>
                    <TableHead className="font-black uppercase text-[10px]">Description</TableHead>
                    <TableHead className="font-black uppercase text-[10px]">Parties</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {caseData.produced_exhibits.map((ex) => (
                    <TableRow key={ex.id} className="hover:bg-slate-50/50 transition-colors">
                      <TableCell className="font-black text-primary">{ex.label}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-white font-bold text-[10px]">{ex.exhibit_type}</Badge>
                      </TableCell>
                      <TableCell className="text-sm font-medium text-slate-600">{ex.date_display}</TableCell>
                      <TableCell className="text-sm max-w-md italic text-slate-700 leading-relaxed">
                        {ex.description}
                      </TableCell>
                      <TableCell className="text-[11px] font-bold text-slate-500">{ex.parties}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="contestations" className="mt-0 space-y-6">
          {caseData.contestations.map((con) => (
            <Card key={con.id} className="border-l-4 border-l-orange-500 shadow-md">
              <CardHeader className="flex flex-row items-center justify-between bg-slate-50/30">
                <div>
                  <CardTitle className="text-xl font-bold">{con.title}</CardTitle>
                  <CardDescription className="font-medium">Perjury Contestation Analysis</CardDescription>
                </div>
                <Button variant="ghost" size="sm" className="font-bold text-primary">Edit Argument</Button>
              </CardHeader>
              <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-1">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">1. Solemn Declaration</h4>
                    <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border italic">"{con.final_sec1_declaration}"</p>
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">2. Contradictory Proof</h4>
                    <p className="text-sm text-slate-700 bg-blue-50/30 p-3 rounded-lg border border-blue-100 leading-relaxed">{con.final_sec2_proof}</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="space-y-1">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">3. Mens Rea (Knowledge of Falsity)</h4>
                    <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border leading-relaxed">{con.final_sec3_mens_rea}</p>
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest">4. Intent to Mislead</h4>
                    <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg border leading-relaxed">{con.final_sec4_intent}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          <Button className="w-full py-8 border-2 border-dashed border-slate-200 bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-slate-600 font-bold" variant="ghost">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Initialize New Perjury Contestation
          </Button>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CaseDashboard;
