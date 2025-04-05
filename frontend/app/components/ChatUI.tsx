'use client';

import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiEdit2 } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ChatUIProps {
  chatId: string;
  initialMessages?: Message[];
}

const ChatUI: React.FC<ChatUIProps> = ({ chatId, initialMessages = [] }) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [input, setInput] = useState<string>('');
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isInitialFetchRef = useRef<boolean>(true);

  // Fetch chat messages when component mounts or chatId changes
  useEffect(() => {
    const fetchMessages = async () => {
      setIsLoading(true);
      try {
        const chatData = await chatApi.getChat(chatId);
        if (chatData.messages) {
          setMessages(chatData.messages);
        } else {
          setMessages([]);
        }
      } catch (error) {
        console.error('Error fetching chat messages:', error);
        setMessages([]);
      } finally {
        setIsLoading(false);
      }
    };

    isInitialFetchRef.current = true;
    fetchMessages();
  }, [chatId]);

  // Reset scroll behavior when chatId changes
  useEffect(() => {
    isInitialFetchRef.current = true;
  }, [chatId]);

  // Custom message handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    if (editingMessageId) {
      // We are editing an existing message
      await handleEditMessage(editingMessageId, input);
      return;
    }
    
    // Add user message to the UI
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    isInitialFetchRef.current = false; // Mark that we're adding new messages
    
    try {
      // Call our streaming endpoint
      const response = await chatApi.streamChat(chatId, input);
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      // Create a placeholder for the assistant's response
      const assistantMessageId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev, 
        { id: assistantMessageId, role: 'assistant', content: '' }
      ]);
      isInitialFetchRef.current = false; // Mark that we're adding assistant message
      
      // Process the stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim() !== '');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') break;
              
              assistantMessage += data;
              
              // Update the message content
              setMessages((prev) => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: assistantMessage } 
                  : msg
              ));
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in chat stream:', error);
      // Add error message
      setMessages((prev) => [
        ...prev, 
        { id: Date.now().toString(), role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    }
  };

  // Track edited messages
  const [editedMessageIds, setEditedMessageIds] = useState<Set<string>>(new Set());

  // Handle editing and re-sending a message
  const handleEditMessage = async (messageId: string, newContent: string) => {
    try {
      // Find the message to edit
      const messageToEdit = messages.find(msg => msg.id === messageId);
      if (!messageToEdit || messageToEdit.role !== 'user') {
        throw new Error('Cannot edit this message');
      }
      
      // Skip if content hasn't changed
      if (messageToEdit.content === newContent.trim()) {
        setEditingMessageId(null);
        setInput('');
        return;
      }
      
      setIsLoading(true);

      // Track this message as edited
      setEditedMessageIds(prev => new Set(prev).add(messageId));

      // Remove all messages after the edited message
      const editedMsgIndex = messages.findIndex(msg => msg.id === messageId);
      if (editedMsgIndex >= 0) {
        // Keep only up to the edited message, removing all subsequent messages
        setMessages(prev => prev.slice(0, editedMsgIndex + 1));
      }

      // Update the message content locally
      setMessages(prev => prev.map(msg => 
        msg.id === messageId ? { ...msg, content: newContent } : msg
      ));
      
      // Clear editing state
      setEditingMessageId(null);
      setInput('');
      
      // Call the API to update and resend the message
      const response = await chatApi.updateAndResendMessage(chatId, messageId, newContent);
      
      if (!response.ok) {
        console.error('Server error:', await response.text());
        throw new Error(`Failed to update message: ${response.status}`);
      }

      // Create a placeholder for the assistant's response
      const assistantMessageId = (Date.now() + 1).toString();
      setMessages(prev => [
        ...prev, 
        { id: assistantMessageId, role: 'assistant', content: '' }
      ]);
      
      // Process the stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      
      if (reader) {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim() !== '');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') break;
                
                assistantMessage += data;
                
                // Update the message content
                setMessages((prev) => prev.map(msg => 
                  msg.id === assistantMessageId 
                    ? { ...msg, content: assistantMessage } 
                    : msg
                ));
              }
            }
          }
        } catch (streamError) {
          console.error('Error processing stream:', streamError);
          setMessages((prev) => prev.map(msg => 
            msg.id === assistantMessageId 
              ? { ...msg, content: assistantMessage || 'Error receiving full response.' } 
              : msg
          ));
        }
      }
    } catch (error) {
      console.error('Error updating message:', error);
      // Add error message
      setMessages((prev) => [
        ...prev, 
        { id: Date.now().toString(), role: 'assistant', content: 'Sorry, I encountered an error while updating the message. Please try again.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Start editing a message
  const startEditMessage = (messageId: string) => {
    const messageToEdit = messages.find(msg => msg.id === messageId);
    if (messageToEdit && messageToEdit.role === 'user') {
      setEditingMessageId(messageId);
      setInput(messageToEdit.content);
    }
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingMessageId(null);
    setInput('');
  };
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0 && !isInitialFetchRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Edit notification */}
      {editingMessageId && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 text-sm text-yellow-700 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="font-medium">Warning: Editing this message</p>
            <p>All subsequent messages will be deleted. The AI will generate new responses based on your edited message.</p>
          </div>
        </div>
      )}
      
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: `calc(100vh - ${editingMessageId ? '180' : '150'}px)` }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading messages...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <p>No messages yet. Start the conversation!</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id} 
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] rounded-lg p-3 relative group ${
                  message.role === 'user' 
                    ? `bg-primary-500 text-white ${editingMessageId === message.id ? 'ring-2 ring-yellow-400' : ''}` 
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                {message.role === 'user' && !isLoading && (
                  <button
                    onClick={() => startEditMessage(message.id)}
                    className="absolute top-2 right-2 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-primary-600/80 text-white hover:bg-primary-700 rounded-full"
                    aria-label="Edit message"
                  >
                    <FiEdit2 size={14} />
                  </button>
                )}
                {message.content ? (
                  <ReactMarkdown className="prose">
                    {message.content}
                  </ReactMarkdown>
                ) : message.role === 'assistant' && isLoading ? (
                  <div className="flex items-center">
                    <div className="animate-pulse flex space-x-1">
                      <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                      <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                      <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                    </div>
                    <span className="ml-2 text-sm text-gray-500">AI is thinking...</span>
                  </div>
                ) : null}
                {editedMessageIds.has(message.id) && (
                  <div className="text-xs mt-1 text-right">
                    <span className={`${message.role === 'user' ? 'text-white/80' : 'text-gray-600'} font-medium px-1.5 py-0.5 rounded-full border ${message.role === 'user' ? 'border-white/30' : 'border-gray-300'}`}>
                      edited
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message input */}
      <div className="border-t border-gray-200 p-4">
        <form 
          onSubmit={handleSubmit}
          className="flex items-center"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={editingMessageId ? "Edit your message..." : "Type your message..."}
            className={`flex-1 border ${editingMessageId ? 'border-yellow-400' : 'border-gray-300'} rounded-l-lg py-2 px-4 focus:outline-none focus:ring-2 ${editingMessageId ? 'focus:ring-yellow-400' : 'focus:ring-primary-500'}`}
            required
          />
          {editingMessageId && (
            <button
              type="button"
              onClick={cancelEdit}
              className="bg-gray-300 text-gray-700 px-3 py-2.5 hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className={`${editingMessageId ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-primary-500 hover:bg-primary-600'} text-white rounded-r-lg p-2.5 focus:outline-none focus:ring-2 ${editingMessageId ? 'focus:ring-yellow-400' : 'focus:ring-primary-500'}`}
          >
            <FiSend size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatUI; 