import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import api from '../services/api';

export interface UserProfile {
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (token: string, refresh: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function tokenIsAlive(token: string): boolean {
  try {
    const decoded: any = jwtDecode(token);
    return decoded.exp ? decoded.exp * 1000 > Date.now() : true;
  } catch {
    return false;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && tokenIsAlive(token)) {
      api.get('/users/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setLoading(false));
    } else {
      if (token) {
        // expired — clean up
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
      setLoading(false);
    }
  }, []);

  const login = async (token: string, refresh: string): Promise<void> => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh);
    const res = await api.get('/users/me');
    setUser(res.data);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
