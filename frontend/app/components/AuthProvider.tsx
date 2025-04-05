'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '../lib/api';
import { toast } from 'react-hot-toast';
import Cookies from 'js-cookie';

interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: Partial<User>) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  confirmPasswordReset: (token: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Store token in both localStorage and cookie
  const setToken = (token: string) => {
    localStorage.setItem('token', token);
    // Set cookie with 7-day expiry, http-only for security
    Cookies.set('token', token, { expires: 7, path: '/' });
  };

  // Remove token from both localStorage and cookie
  const removeToken = () => {
    localStorage.removeItem('token');
    Cookies.remove('token');
  };

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsLoading(false);
          return;
        }

        const user = await authApi.me();
        setUser(user);
      } catch (error) {
        console.error('Authentication error:', error);
        removeToken();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await authApi.login(username, password);
      setToken(result.access_token);
      
      // Fetch user data
      const user = await authApi.me();
      setUser(user);
      
      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please check your credentials.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, username: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      await authApi.register(email, username, password, fullName);
      toast.success('Registration successful! Please verify your email.');
      router.push('/auth/login');
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('Registration failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    removeToken();
    setUser(null);
    router.push('/');
    toast.success('Logged out successfully');
  };

  const updateProfile = async (data: Partial<User>) => {
    setIsLoading(true);
    try {
      const updatedUser = await authApi.updateProfile(data);
      setUser(updatedUser);
      toast.success('Profile updated successfully');
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error('Failed to update profile');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const verifyEmail = async (token: string) => {
    setIsLoading(true);
    try {
      const user = await authApi.verifyEmail(token);
      toast.success('Email verified successfully!');
      return user;
    } catch (error) {
      console.error('Email verification error:', error);
      toast.error('Failed to verify email');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const requestPasswordReset = async (email: string) => {
    setIsLoading(true);
    try {
      await authApi.requestPasswordReset(email);
      toast.success('Password reset link sent to your email');
    } catch (error) {
      console.error('Password reset request error:', error);
      toast.error('Failed to request password reset');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const confirmPasswordReset = async (token: string, newPassword: string) => {
    setIsLoading(true);
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      toast.success('Password reset successful! Please login.');
      router.push('/auth/login');
    } catch (error) {
      console.error('Password reset confirmation error:', error);
      toast.error('Failed to reset password');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isLoading, 
      login, 
      register, 
      logout, 
      updateProfile,
      verifyEmail,
      requestPasswordReset,
      confirmPasswordReset
    }}>
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