'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiPlus, FiLogOut, FiSettings, FiTrash2 } from 'react-icons/fi';
import Link from 'next/link';
import ChatUI from '../components/ChatUI';
import { chatApi } from '../lib/api';
import { useAuth } from '../components/AuthProvider';
import toast from 'react-hot-toast';

interface Chat {
  id: string;
  title: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Fetch chats on load
  useEffect(() => {
    const fetchChats = async () => {
      try {
        setIsLoading(true);
        const response = await chatApi.getChats();
        setChats(response.chats || []);
        
        // If no active chat and we have chats, set the first one active
        if (response.chats && response.chats.length > 0 && !currentChat) {
          setCurrentChat(response.chats[0].id);
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
        toast.error('Failed to load chats');
      } finally {
        setIsLoading(false);
      }
    };
    
    if (user) {
      fetchChats();
    }
  }, [user]);
  
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

  const handleDeleteChat = async (chatId: string, e: React.MouseEvent) => {
    // Prevent the click from triggering chat selection
    e.stopPropagation();
    
    try {
      // Confirm deletion
      if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        return;
      }
      
      // Delete the chat
      await chatApi.deleteChat(chatId);
      
      // Remove the chat from the state
      const updatedChats = chats.filter((chat) => chat.id !== chatId);
      setChats(updatedChats);
      
      // If the current chat is deleted, select the first available chat or null
      if (currentChat === chatId) {
        setCurrentChat(updatedChats.length > 0 ? updatedChats[0].id : null);
      }
      
      // Show success message
      toast.success('Chat deleted successfully');
    } catch (error) {
      console.error('Error deleting chat:', error);
      toast.error('Failed to delete chat');
    }
  };
  
  // Render loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
          <p className="mt-3 text-gray-600">Loading your chats...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Conversations</h2>
          <button
            onClick={handleNewChat}
            className="mt-3 w-full bg-primary-500 text-white rounded-md py-2 hover:bg-primary-600 transition-colors flex items-center justify-center"
          >
            <FiPlus className="mr-2" /> New Chat
          </button>
        </div>
        
        <div className="overflow-y-auto flex-grow">
          {chats.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              No conversations yet. Start a new chat!
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {chats.map((chat) => (
                <li key={chat.id}>
                  <div className={`flex items-center p-4 hover:bg-gray-50 transition-colors ${
                    currentChat === chat.id ? 'bg-gray-100' : ''
                  }`}>
                    <button
                      onClick={() => setCurrentChat(chat.id)}
                      className="flex-grow text-left"
                    >
                      <p className="font-medium text-gray-800 truncate">{chat.title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(chat.created_at).toLocaleDateString()}
                      </p>
                    </button>
                    <button
                      onClick={(e) => handleDeleteChat(chat.id, e)}
                      className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-gray-100 rounded"
                      title="Delete chat"
                    >
                      <FiTrash2 size={18} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-200">
          <Link
            href="/settings"
            className="flex items-center text-gray-600 hover:text-gray-800 mb-4 text-sm"
          >
            <FiSettings className="mr-2" /> Settings
          </Link>
          <button
            onClick={logout}
            className="flex items-center w-full text-gray-600 hover:text-gray-800 text-sm"
          >
            <FiLogOut className="mr-2" /> Log Out
          </button>
        </div>
      </div>
      
      {/* Chat Area */}
      <div className="flex-1 overflow-hidden">
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
  );
} 