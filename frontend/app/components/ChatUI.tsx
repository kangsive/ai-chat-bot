'use client';

import React, { useState, useRef, useEffect } from 'react';
import { FiSend } from 'react-icons/fi';
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
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0 && !isInitialFetchRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length]);

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ maxHeight: 'calc(100vh - 150px)' }}>
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
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                <ReactMarkdown className="prose">
                  {message.content}
                </ReactMarkdown>
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
            placeholder="Type your message..."
            className="flex-1 border border-gray-300 rounded-l-lg py-2 px-4 focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          />
          <button
            type="submit"
            className="bg-primary-500 text-white rounded-r-lg p-2.5 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <FiSend size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatUI; 