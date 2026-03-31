import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, FileText, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ProducedExhibit {
  id: number;
  label: string;
  exhibit_type: string;
  date_display: string;
  description: string;
  parties: string;
}

interface CaseData {
  id: number;
  title: string;
  created_at: string;
  produced_exhibits: ProducedExhibit[];
}

const CaseDetailView: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCaseDetail = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/cases/${caseId}`);
        setCaseData(response.data);
        setError(null);
      } catch (err: any) {
        if (err.response?.status === 401) {
          logout();
          navigate('/login');
        } else {
          setError(err.response?.data?.message || 'Failed to fetch case details.');
        }
      } finally {
        setLoading(false);
      }
    };

    if (caseId) fetchCaseDetail();
  }, [caseId, logout, navigate]);

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-4">
        <Skeleton className="h-10 w-[250px]" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-[200px]" />
            <Skeleton className="h-4 w-[300px]" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-[400px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={() => navigate('/')} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={() => navigate('/')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <Badge variant="outline" className="text-sm">
          Case ID: {caseData?.id}
        </Badge>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center space-x-4">
          <div className="p-2 bg-primary/10 rounded-full">
            <FileText className="h-8 w-8 text-primary" />
          </div>
          <div>
            <CardTitle className="text-2xl">{caseData?.title}</CardTitle>
            <CardDescription>
              Opened on {caseData ? new Date(caseData.created_at).toLocaleDateString() : ''}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <h3 className="text-lg font-semibold border-b pb-2">Exhibit Registry (Calculated)</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Cote</TableHead>
                  <TableHead className="w-[120px]">Type</TableHead>
                  <TableHead className="w-[150px]">Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Parties</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {caseData?.produced_exhibits.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No exhibits produced for this case.
                    </TableCell>
                  </TableRow>
                ) : (
                  caseData?.produced_exhibits.map((exhibit) => (
                    <TableRow key={exhibit.id}>
                      <TableCell className="font-bold text-primary">
                        {exhibit.label}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{exhibit.exhibit_type}</Badge>
                      </TableCell>
                      <TableCell className="text-sm">{exhibit.date_display}</TableCell>
                      <TableCell className="max-w-md truncate" title={exhibit.description}>
                        {exhibit.description}
                      </TableCell>
                      <TableCell className="text-sm italic">{exhibit.parties}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CaseDetailView;
