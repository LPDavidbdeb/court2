import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Folder, FileText, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AnnotatedNode {
  id: number;
  item: string;
  depth: number;
  info: {
    open: boolean;
    close: boolean[];
  };
}

const DocumentTreeView: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [treeData, setTreeData] = useState<AnnotatedNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTree = async () => {
      try {
        const response = await api.get(`/documents/${documentId}/tree`);
        setTreeData(response.data);
      } catch (err) {
        console.error("Failed to fetch tree", err);
      } finally {
        setLoading(false);
      }
    };
    if (documentId) fetchTree();
  }, [documentId]);

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-4">
        <Skeleton className="h-10 w-[200px]" />
        <Card>
          <CardHeader><Skeleton className="h-6 w-1/3" /></CardHeader>
          <CardContent className="space-y-2">
            {[1, 2, 3, 4, 5].map(i => <Skeleton key={i} className="h-6 w-full" />)}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Button variant="ghost" onClick={() => navigate('/')}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Dashboard
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Document Hierarchy (Treebeard)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border rounded-md p-4 bg-slate-50/50 space-y-1">
            {treeData.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No hierarchy defined for this document.</p>
            ) : (
              treeData.map((node) => (
                <div 
                  key={node.id} 
                  className="flex items-center py-1 px-2 hover:bg-white rounded transition-colors"
                  style={{ marginLeft: `${(node.depth - 1) * 1.5}rem` }}
                >
                  {/* Treebeard depth starts at 1 */}
                  <div className="flex items-center text-sm">
                    {node.info.open ? (
                       <Folder className="h-4 w-4 text-blue-500 mr-2" />
                    ) : (
                       <FileText className="h-4 w-4 text-slate-400 mr-2" />
                    )}
                    <span className={node.info.open ? 'font-medium' : ''}>
                      {node.item}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentTreeView;
