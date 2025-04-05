"use client";

import axios from 'axios';

// Get token from client-side storage
const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

// Base API client
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authorization header when token is available
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post('/users/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  register: async (email: string, username: string, password: string, fullName?: string) => {
    const response = await apiClient.post('/users', {
      email,
      username,
      password,
      full_name: fullName,
    });
    return response.data;
  },
  
  me: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },
  
  updateProfile: async (data: any) => {
    const response = await apiClient.put('/users/me', data);
    return response.data;
  },

  verifyEmail: async (token: string) => {
    const response = await apiClient.post('/users/verify-email', { token });
    return response.data;
  },

  requestPasswordReset: async (email: string) => {
    const response = await apiClient.post('/users/reset-password', { email });
    return response.data;
  },

  confirmPasswordReset: async (token: string, newPassword: string) => {
    const response = await apiClient.post('/users/reset-password/confirm', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },
};

// Chat API
export const chatApi = {
  getChats: async () => {
    const response = await apiClient.get('/chats');
    return response.data;
  },
  
  getChat: async (chatId: string) => {
    const response = await apiClient.get(`/chats/${chatId}`);
    return response.data;
  },
  
  createChat: async (title?: string) => {
    const response = await apiClient.post('/chats', { title });
    return response.data;
  },
  
  updateChat: async (chatId: string, data: any) => {
    const response = await apiClient.put(`/chats/${chatId}`, data);
    return response.data;
  },
  
  deleteChat: async (chatId: string) => {
    const response = await apiClient.delete(`/chats/${chatId}`);
    return response.data;
  },
  
  createMessage: async (chatId: string, content: string, role: string = 'user') => {
    const response = await apiClient.post(`/chats/${chatId}/messages`, {
      chat_id: chatId,
      content,
      role,
      sequence: 0, // Will be set by the backend
    });
    return response.data;
  },
  
  // Stream chat
  streamChat: async (chatId: string, message: string) => {
    return fetch(`${apiClient.defaults.baseURL}/chats/${chatId}/chat?message_content=${encodeURIComponent(message)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
      },
    });
  },
};

// Config API
export const configApi = {
  getUserConfig: async () => {
    const response = await apiClient.get('/config/user');
    return response.data;
  },
  
  updateUserConfig: async (preferences: any) => {
    const response = await apiClient.put('/config/user', { preferences });
    return response.data;
  },
}; 