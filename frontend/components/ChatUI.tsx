import React, { useState, useRef, useEffect } from 'react';
import { useChat } from 'ai/react';
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Custom message handler for the Vercel AI SDK
  const handleSubmit = async (message: string) => {
    // Add user message to the UI
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: message,
    };
    
    setMessages((prev) => [...prev, userMessage]);
    
    try {
      // Call our streaming endpoint
      const response = await chatApi.streamChat(chatId, message);
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      // Create a placeholder for the assistant's response
      const assistantMessageId = (Date.now() + 1).toString();
      setMessages((prev) => [
        ...prev, 
        { id: assistantMessageId, role: 'assistant', content: '' }
      ]);
      
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
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
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
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Message input */}
      <div className="border-t border-gray-200 p-4">
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            const form = e.target as HTMLFormElement;
            const input = form.elements.namedItem('message') as HTMLInputElement;
            const message = input.value.trim();
            if (message) {
              handleSubmit(message);
              input.value = '';
            }
          }}
          className="flex items-center"
        >
          <input
            name="message"
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