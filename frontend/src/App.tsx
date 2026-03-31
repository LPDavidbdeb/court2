import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { useState } from 'react';
import api from './services/api';
import Layout from './components/Layout';
import PhotoDocumentList from './pages/PhotoDocumentList';
import PhotoDocumentDetail from './pages/PhotoDocumentDetail';
import { Gavel } from 'lucide-react';

const Home = () => {
  const { user } = useAuth();
  return (
    <div className="flex flex-col space-y-2">
      <h1 className="text-2xl font-bold text-slate-900">Welcome to My Court Application!</h1>
      <p className="text-slate-500">Logged in as {user?.email}.</p>
    </div>
  );
};

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="h-screen w-screen flex items-center justify-center font-bold text-primary animate-pulse">Authenticating...</div>;
  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

const Login = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  // Already authenticated → go home
  if (isAuthenticated) return <Navigate to="/" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.post('/token/pair', { email, password });
      login(res.data.access, res.data.refresh);
      navigate('/', { replace: true });
    } catch {
      setError('Email ou mot de passe invalide. Accès refusé.');
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-slate-100">
      <Card className="w-[400px] shadow-lg">
        <CardHeader className="space-y-2 pb-4">
          <div className="flex justify-center mb-2">
            <Gavel className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-2xl font-bold text-center">Log In</CardTitle>
          <p className="text-center text-slate-500 text-sm">Accès réservé aux utilisateurs autorisés.</p>
          <hr className="border-slate-200" />
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email address</label>
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full p-3 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full p-3 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex flex-col gap-2 mt-4">
              <Button type="submit" className="w-full">
                Log In
              </Button>
              <a
                href="/accounts/password/reset/"
                className="text-center text-sm text-slate-500 hover:text-primary underline"
              >
                Forgot Password?
              </a>
            </div>
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
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/photos/documents" element={<PrivateRoute><PhotoDocumentList /></PrivateRoute>} />
          <Route path="/photos/documents/:docId" element={<PrivateRoute><PhotoDocumentDetail /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;