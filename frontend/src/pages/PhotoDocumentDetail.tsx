import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../components/ui/card';

// ── Types ─────────────────────────────────────────────────────────────────────

interface PhotoItem {
  id: number;
  file_name: string;
  file_url: string | null;
  width: number | null;
  height: number | null;
}

interface PhotoDocumentDetail {
  id: number;
  title: string;
  description: string | null;
  ai_analysis: string | null;
  created_at: string;
  photos: PhotoItem[];
}

// ── Persona definitions (must match backend AI_PERSONAS keys exactly) ─────────

const PERSONAS = [
  { value: 'forensic_clerk',  label: '🔍 Greffier Forensique (Description)' },
  { value: 'official_scribe', label: '📜 Scribe Officiel (Transcription)' },
  { value: 'summary_clerk',   label: '📝 Secrétaire (Résumé)' },
] as const;

// ── Inline Rich-Text Editor ───────────────────────────────────────────────────
//
// Replicates the legacy TinyMCE inline behaviour:
//   - Click description area  → enters edit mode
//   - Toolbar: bold, italic, underline, unordered list, ordered list
//   - Blur                    → auto-saves via PATCH /photos/documents/{id}/description/
//
// execCommand is used to match the exact feature set of the legacy TinyMCE
// toolbar (undo redo | bold italic underline | bullist numlist).

interface InlineDescriptionEditorProps {
  docId: number;
  initialContent: string;
  onSave: (newContent: string) => void;
}

function InlineDescriptionEditor({ docId, initialContent, onSave }: InlineDescriptionEditorProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [content, setContent] = useState(initialContent);
  const editorRef = useRef<HTMLDivElement>(null);

  // When entering edit mode, populate the contentEditable element
  useEffect(() => {
    if (isEditing && editorRef.current) {
      editorRef.current.innerHTML = content;
      editorRef.current.focus();
    }
  }, [isEditing]);

  const handleBlur = async () => {
    const newContent = editorRef.current?.innerHTML ?? '';
    if (newContent === content) {
      setIsEditing(false);
      return;
    }
    setIsSaving(true);
    try {
      await api.patch(`/photos/documents/${docId}/description/`, { description: newContent });
      setContent(newContent);
      onSave(newContent);
    } catch {
      alert('Erreur lors de la sauvegarde de la description.');
    } finally {
      setIsSaving(false);
      setIsEditing(false);
    }
  };

  // Prevent toolbar button clicks from blurring the editor
  const execFormat = (command: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    document.execCommand(command, false, undefined);
    editorRef.current?.focus();
  };

  return (
    <div>
      {isEditing && (
        <div className="flex gap-1 mb-2 p-1 border border-slate-200 rounded bg-slate-50 w-fit">
          <button
            onMouseDown={execFormat('bold')}
            className="px-2 py-1 text-sm font-bold hover:bg-slate-200 rounded"
            title="Bold"
          >B</button>
          <button
            onMouseDown={execFormat('italic')}
            className="px-2 py-1 text-sm italic hover:bg-slate-200 rounded"
            title="Italic"
          >I</button>
          <button
            onMouseDown={execFormat('underline')}
            className="px-2 py-1 text-sm underline hover:bg-slate-200 rounded"
            title="Underline"
          >U</button>
          <div className="w-px bg-slate-300 mx-1" />
          <button
            onMouseDown={execFormat('insertUnorderedList')}
            className="px-2 py-1 text-sm hover:bg-slate-200 rounded"
            title="Unordered list"
          >• List</button>
          <button
            onMouseDown={execFormat('insertOrderedList')}
            className="px-2 py-1 text-sm hover:bg-slate-200 rounded"
            title="Ordered list"
          >1. List</button>
        </div>
      )}

      {isEditing ? (
        <div
          ref={editorRef}
          contentEditable
          onBlur={handleBlur}
          className="min-h-[80px] p-3 border border-primary rounded-md outline-none prose prose-sm max-w-none"
          suppressContentEditableWarning
        />
      ) : (
        <div
          onClick={() => setIsEditing(true)}
          title="Click to edit"
          className="min-h-[40px] cursor-pointer p-2 rounded hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-colors prose prose-sm max-w-none"
        >
          {content ? (
            <div dangerouslySetInnerHTML={{ __html: content }} />
          ) : (
            <p className="text-slate-400 italic">No description provided. Click to add one.</p>
          )}
        </div>
      )}

      {isSaving && (
        <p className="text-xs text-slate-400 mt-1">Sauvegarde en cours...</p>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function PhotoDocumentDetail() {
  const { docId } = useParams<{ docId: string }>();
  const [doc, setDoc] = useState<PhotoDocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // AI Analysis state
  const [persona, setPersona] = useState<string>('forensic_clerk');
  const [analysisText, setAnalysisText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    api.get(`/photos/documents/${docId}/`)
      .then(res => {
        setDoc(res.data);
        setAnalysisText(res.data.ai_analysis ?? 'Aucune analyse.');
      })
      .catch(() => setError('Failed to load document.'))
      .finally(() => setLoading(false));
  }, [docId]);

  const analyzeDocument = async () => {
    if (!doc) return;
    setAnalyzing(true);
    try {
      const res = await api.post(`/photos/documents/${doc.id}/analyze/`, { persona });
      if (res.data.status === 'success') {
        setAnalysisText(res.data.analysis ?? '');
      } else {
        setAnalysisText('Error: ' + (res.data.message ?? 'Analysis failed.'));
      }
    } catch {
      setAnalysisText('An unexpected error occurred.');
    } finally {
      setAnalyzing(false);
    }
  };

  const clearAnalysis = async () => {
    if (!doc || !confirm('Are you sure you want to delete this AI analysis?')) return;
    setClearing(true);
    try {
      const res = await api.delete(`/photos/documents/${doc.id}/analyze/`);
      if (res.data.status === 'success') {
        setAnalysisText('Aucune analyse.');
      }
    } catch {
      alert('An unexpected error occurred.');
    } finally {
      setClearing(false);
    }
  };

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (error || !doc) return <div className="p-8 text-red-600">{error || 'Document not found.'}</div>;

  return (
    <div className="max-w-4xl">
      <Card className="shadow-sm">
        <CardHeader className="bg-primary text-primary-foreground">
          <CardTitle className="text-lg font-bold">{doc.title}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">

          {/* Description — Inline editable */}
          <section>
            <h5 className="text-sm font-semibold text-slate-700 mb-2">Description</h5>
            <InlineDescriptionEditor
              docId={doc.id}
              initialContent={doc.description ?? ''}
              onSave={(newContent) => setDoc(prev => prev ? { ...prev, description: newContent } : prev)}
            />
          </section>

          <hr className="border-slate-200" />

          {/* AI Analysis */}
          <section>
            <h5 className="text-sm font-semibold text-slate-700 mb-3">AI Analysis</h5>
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <select
                value={persona}
                onChange={e => setPersona(e.target.value)}
                className="border border-slate-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {PERSONAS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>

              <Button
                onClick={analyzeDocument}
                disabled={analyzing}
                variant="outline"
                size="sm"
              >
                {analyzing ? 'Analyse en cours...' : '🤖 Analyser'}
              </Button>

              <Button
                onClick={clearAnalysis}
                disabled={clearing}
                variant="outline"
                size="sm"
                className="text-red-600 border-red-300 hover:bg-red-50"
              >
                🗑️ Effacer
              </Button>
            </div>

            <div className="p-3 bg-slate-50 rounded-md text-sm whitespace-pre-wrap font-mono">
              {analysisText || 'Aucune analyse.'}
            </div>
          </section>

          <hr className="border-slate-200" />

          {/* Photo Gallery */}
          <section>
            <h5 className="text-sm font-semibold text-slate-700 mb-3">Associated Photos</h5>
            {doc.photos.length === 0 ? (
              <p className="text-slate-400 text-sm">There are no photos associated with this document.</p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {doc.photos.map(photo => (
                  <div key={photo.id} className="rounded-md overflow-hidden border border-slate-200 shadow-sm">
                    {photo.file_url ? (
                      <img
                        src={photo.file_url}
                        alt={photo.file_name}
                        className="w-full h-48 object-cover"
                      />
                    ) : (
                      <div className="w-full h-48 bg-slate-100 flex items-center justify-center text-slate-400 text-xs">
                        No image
                      </div>
                    )}
                    <div className="px-2 py-1 bg-slate-50 text-xs text-slate-500 truncate">
                      {photo.file_name}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

        </CardContent>

        <CardFooter className="flex gap-2 border-t bg-slate-50/50">
          <Link to="/photos/documents">
            <Button variant="secondary" size="sm">Back to List</Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
