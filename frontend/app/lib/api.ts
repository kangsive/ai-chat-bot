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
  
  // Unified message API - handles both creating messages and getting LLM responses
  sendMessage: async (chatId: string, content: string, files?: File[], sequence?: number) => {
    // Create the message data
    const messageData = {
      role: "user",
      content: content,
      sequence: sequence || null
    };
    
    // Create form data for the files if they exist
    const formData = new FormData();
    
    // Add the message as a JSON string
    formData.append('message', JSON.stringify(messageData));
    
    // Add files if they exist
    if (files && files.length > 0) {
      files.forEach(file => {
        formData.append('files', file);
      });
    }
    
    return fetch(`${apiClient.defaults.baseURL}/chats/${chatId}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      },
      body: formData,
    });
  },
  
  // Delete a specific attachment from a message
  deleteAttachment: async (chatId: string, messageId: string, attachmentId: string) => {
    return fetch(`${apiClient.defaults.baseURL}/chats/${chatId}/messages/${messageId}/attachments/${attachmentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
  }
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

// Add file upload methods to the API client
export const fileApi = {
  /* 
   * Note on API client usage:
   * - apiClient (axios) is used for regular JSON API calls with automatic handling of base URL and auth
   * - fetch is used for file uploads and streaming responses that go through Next.js API routes (/api/v1/...)
   * - File upload endpoints use relative URLs that are proxied through Next.js to the backend
   */
  uploadAttachment: async (chatId: string, messageId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`/api/v1/chats/${chatId}/messages/${messageId}/attachments`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to upload file: ${response.statusText}`);
    }
    
    return await response.json();
  },
  
  downloadAttachment: async (attachmentId: string) => {
    return await fetch(`${apiClient.defaults.baseURL}/chats/attachments/${attachmentId}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
  },
  
  deleteAttachment: async (attachmentId: string) => {
    const response = await fetch(`${apiClient.defaults.baseURL}/chats/attachments/${attachmentId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete attachment: ${response.statusText}`);
    }
    
    return await response.json();
  }
}; 