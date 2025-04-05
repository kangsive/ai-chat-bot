import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import ChatUI from '../components/ChatUI';
import { chatApi } from '../lib/api';
import toast from 'react-hot-toast';

interface Chat {
  id: string;
  title: string;
  created_at: string;
}

const DashboardPage: React.FC = () => {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch chats on load
  useEffect(() => {
    const fetchChats = async () => {
      try {
        // Check if token exists
        const token = localStorage.getItem('token');
        if (!token) {
          router.push('/login');
          return;
        }
        
        const response = await chatApi.getChats();
        setChats(response.chats || []);
        
        // If no active chat and we have chats, set the first one active
        if (response.chats && response.chats.length > 0 && !currentChat) {
          setCurrentChat(response.chats[0].id);
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
        toast.error('Failed to load chats');
        
        // If unauthorized, redirect to login
        if ((error as any)?.response?.status === 401) {
          localStorage.removeItem('token');
          router.push('/login');
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchChats();
  }, [router]);
  
  const handleNewChat = async () => {
    try {
      // Create a chat with a more descriptive title
      const newChat = await chatApi.createChat(`New Chat ${new Date().toLocaleString()}`);
      
      // Add the new chat to the beginning of the chats array
      setChats((prev) => [newChat, ...prev]);
      
      // Set the current chat to the new chat
      setCurrentChat(newChat.id);
      
      // Show success notification
      toast.success('New chat created');
    } catch (error) {
      console.error('Error creating chat:', error);
      toast.error('Failed to create new chat');
    }
  };
  
  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };
  
  // Render loading state
  if (isLoading) {
    return (
      <Layout title="AI Chatbot - Dashboard">
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
            <p className="mt-3 text-gray-600">Loading your chats...</p>
          </div>
        </div>
      </Layout>
    );
  }
  
  return (
    <Layout title="AI Chatbot - Dashboard">
      <div className="flex h-screen bg-gray-100">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">Conversations</h2>
            <button
              onClick={handleNewChat}
              className="mt-3 w-full bg-primary-500 text-white rounded-md py-2 hover:bg-primary-600 transition-colors"
            >
              New Chat
            </button>
          </div>
          
          <div className="overflow-y-auto h-[calc(100vh-12rem)]">
            {chats.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No conversations yet. Start a new chat!
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {chats.map((chat) => (
                  <li key={chat.id}>
                    <button
                      onClick={() => setCurrentChat(chat.id)}
                      className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                        currentChat === chat.id ? 'bg-gray-100' : ''
                      }`}
                    >
                      <p className="font-medium text-gray-800 truncate">{chat.title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(chat.created_at).toLocaleDateString()}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={handleLogout}
              className="w-full text-gray-600 hover:text-gray-800 text-sm"
            >
              Log Out
            </button>
          </div>
        </div>
        
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {currentChat ? (
            <ChatUI key={currentChat} chatId={currentChat} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h3 className="text-xl font-medium text-gray-800">No chat selected</h3>
                <p className="mt-2 text-gray-600">
                  Select a conversation from the sidebar or start a new one.
                </p>
                <button
                  onClick={handleNewChat}
                  className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
                >
                  Start New Chat
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default DashboardPage; 