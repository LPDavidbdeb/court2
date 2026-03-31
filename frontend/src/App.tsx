import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { useEffect, useState } from 'react';
import api from './services/api';
import CaseDetail from './pages/CaseDetail';
import DocumentTree from './pages/DocumentTree';
import EmailThreads from './pages/EmailThreads';
import EmailThreadDetail from './pages/EmailThreadDetail';
import Events from './pages/Events';
import EventDetail from './pages/EventDetail';
import Layout from './components/Layout';
import { Mail, FileText, Briefcase, CalendarDays, ArrowRight } from 'lucide-react';
import TimelineView from './components/TimelineView';
import EvidenceGallery from './components/EvidenceGallery';

const Dashboard = () => {
  const [cases, setCases] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const { user } = useAuth();

  useEffect(() => {
    api.get('/cases/').then((res) => setCases(res.data));
    api.get('/documents/').then((res) => setDocuments(res.data));
    api.get('/events/').then((res) => setEvents(res.data.slice(0, 5)));
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-in fade-in duration-700">
      <div className="flex flex-col space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">Command Center</h1>
        <p className="text-slate-500 text-lg font-medium">Hello, {user?.email}. Monitoring {cases.length} active legal files.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="hover:shadow-lg transition-all border-none bg-blue-600 text-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest opacity-80">Evidence Inbox</CardTitle>
            <Mail className="h-5 w-5 opacity-80" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-6">Email Registry</div>
            <Link to="/emails/threads">
              <Button variant="secondary" className="w-full font-bold bg-white text-blue-600 hover:bg-blue-50 border-none">
                Browse Threads
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all border-none bg-orange-500 text-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest opacity-80">Chronology</CardTitle>
            <CalendarDays className="h-5 w-5 opacity-80" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-6">Events Timeline</div>
            <Link to="/events">
              <Button variant="secondary" className="w-full font-bold bg-white text-orange-600 hover:bg-orange-50 border-none">
                View History
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-all border-none bg-slate-800 text-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-bold uppercase tracking-widest opacity-80">Archives</CardTitle>
            <FileText className="h-5 w-5 opacity-80" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold mb-6">Legal Library</div>
            <div className="space-y-2 mb-4">
               {documents.slice(0, 2).map(d => (
                 <div key={d.id} className="text-xs flex justify-between items-center opacity-90 font-medium">
                   <span className="truncate max-w-[180px]">{d.title}</span>
                   <ArrowRight className="h-3 w-3" />
                 </div>
               ))}
            </div>
            <Button variant="secondary" className="w-full font-bold bg-white text-slate-800 hover:bg-slate-100 border-none">
              Explore Docs
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="border-b bg-slate-50/50">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-purple-600" />
              Active Legal Cases
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {cases.map((c) => (
                <div key={c.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors group">
                  <div className="flex flex-col">
                    <span className="font-bold text-slate-900 group-hover:text-primary transition-colors">{c.title}</span>
                    <span className="text-xs text-slate-500">Case ID: L-{c.id} • {new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                  <Link to={`/cases/${c.id}`}>
                    <Button variant="ghost" size="sm" className="font-bold">Details</Button>
                  </Link>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-slate-200">
          <CardHeader className="border-b bg-slate-50/50">
            <CardTitle className="text-lg font-bold flex items-center gap-2">
              <CalendarDays className="h-5 w-5 text-orange-600" />
              Recent Timeline Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-100">
              {events.map((e) => (
                <div key={e.id} className="p-4 flex flex-col space-y-1 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between">
                    <span className="text-xs font-bold text-slate-400">{new Date(e.date).toLocaleDateString()}</span>
                    {e.linked_email_id && <Badge variant="secondary" className="text-[9px] uppercase h-4">Email</Badge>}
                  </div>
                  <p className="text-sm text-slate-700 line-clamp-1 italic">"{e.explanation}"</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="h-screen w-screen flex items-center justify-center font-bold text-primary animate-pulse">Initializing Court V2...</div>;
  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

const Login = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/token/pair', { email, password });
      login(res.data.access, res.data.refresh);
    } catch (err) {
      alert('Authentication error. Access denied.');
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-slate-100">
      <Card className="w-[400px] shadow-2xl border-t-8 border-t-primary overflow-hidden">
        <CardHeader className="space-y-2 bg-white pb-8">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-primary/10 rounded-2xl">
              <Briefcase className="h-10 w-10 text-primary" />
            </div>
          </div>
          <CardTitle className="text-3xl font-black text-center tracking-tight">Court Portal</CardTitle>
          <p className="text-center text-slate-400 text-sm font-semibold uppercase tracking-widest">Headless V2 Secure Access</p>
        </CardHeader>
        <CardContent className="bg-white px-8 pb-10">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase ml-1">Terminal ID</label>
              <input 
                type="email" 
                placeholder="operator@system.law" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-xl focus:border-primary focus:bg-white outline-none transition-all font-medium"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-black text-slate-500 uppercase ml-1">Access Key</label>
              <input 
                type="password" 
                placeholder="••••••••••••" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                className="w-full p-4 bg-slate-50 border-2 border-slate-100 rounded-xl focus:border-primary focus:bg-white outline-none transition-all font-medium"
              />
            </div>
            <Button type="submit" className="w-full py-8 text-xl font-black shadow-lg shadow-primary/20 rounded-xl">
              AUTHORIZE ACCESS
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/cases/:caseId" element={<PrivateRoute><CaseDetail /></PrivateRoute>} />
          <Route path="/documents/:documentId/tree" element={<PrivateRoute><DocumentTree /></PrivateRoute>} />
          <Route path="/emails/threads" element={<PrivateRoute><EmailThreads /></PrivateRoute>} />
          <Route path="/emails/threads/:threadId" element={<PrivateRoute><EmailThreadDetail /></PrivateRoute>} />
          <Route path="/events" element={<PrivateRoute><Events /></PrivateRoute>} />
          <Route path="/events/:eventId" element={<PrivateRoute><EventDetail /></PrivateRoute>} />
          <Route path="/timeline" element={<PrivateRoute><TimelineView /></PrivateRoute>} />
          <Route path="/gallery" element={<PrivateRoute><EvidenceGallery /></PrivateRoute>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
