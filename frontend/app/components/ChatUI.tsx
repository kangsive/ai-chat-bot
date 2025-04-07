'use client';

import React, { useEffect, useRef, useState } from 'react';
import { FiEdit, FiSend, FiFile, FiDownload, FiX, FiPaperclip } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { chatApi, fileApi } from '../lib/api';
import axios from 'axios';
import { Message, Attachment } from '../interfaces/chat';

interface ChatUIProps {
  chatId: string;
  initialMessages?: Message[];
}

const ChatUI: React.FC<ChatUIProps> = ({ chatId, initialMessages = [] }) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isInitialFetchRef = useRef<boolean>(true);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingSequence, setEditingSequence] = useState<number | null>(null);
  const [editedMessageIds, setEditedMessageIds] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch messages when chatId changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!chatId) return;
      
      try {
        // Use the API function instead of direct fetch
        const data = await chatApi.getChat(chatId);
        if (data.messages) {
          setMessages(data.messages);
        }
      } catch (error) {
        console.error('Error fetching messages:', error);
      }
    };
    
    fetchMessages();
  }, [chatId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles([...selectedFiles, ...filesArray]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const handleSelectFilesClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleDeleteAttachment = async (attachmentId: string, messageId: string) => {
    try {
      const response = await chatApi.deleteAttachment(chatId, messageId, attachmentId);
      
      if (!response.ok) {
        throw new Error("Failed to delete attachment");
      }
      
      // Update local state to remove the attachment
      setMessages(prevMessages => 
        prevMessages.map(message => {
          if (message.id === messageId && message.attachments) {
            return {
              ...message,
              attachments: message.attachments.filter(att => att.id !== attachmentId)
            };
          }
          return message;
        })
      );
    } catch (error) {
      console.error('Error deleting attachment:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() && selectedFiles.length === 0) return;
    
    // Get the sequence number for the new message
    const nextSequence = messages.length > 0 
      ? Math.max(...messages.map(m => m.sequence || 0)) + 1 
      : 1;
    
    // Using sequence from editing state or null for new messages
    const sequenceToUse = editingSequence;
    
    // Add or update user message in UI immediately
    if (editingSequence !== null) {
      // For editing - update the UI to show the edited message with content only
      // Attachments are handled separately via direct API calls
      const editedIndex = messages.findIndex(msg => msg.sequence === editingSequence);
      if (editedIndex !== -1) {
        // Don't modify the attachments, just update the content
        const updatedMessages = messages.slice(0, editedIndex + 1).map(msg => 
          msg.sequence === editingSequence 
            ? { ...msg, content: input } 
            : msg
        );
        setMessages(updatedMessages);
      }
    } else {
      // For new messages - add to UI
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: input,
        sequence: nextSequence,
        chat_id: chatId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      setMessages([...messages, userMessage]);
    }
    
    setInput('');
    setIsLoading(true);
    
    try {
      // Use the unified API with sequence for editing
      const response = await chatApi.sendMessage(
        chatId, 
        input, 
        selectedFiles, 
        sequenceToUse || undefined
      );
      
      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }
      
      // If we were editing, mark as edited in the UI
      if (editingSequence !== null) {
        const messageId = messages.find(m => m.sequence === editingSequence)?.id;
        if (messageId) {
          setEditedMessageIds(new Set([...Array.from(editedMessageIds), messageId]));
        }
      }
      
      // Create a placeholder for the assistant's response
      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantSequence = editingSequence ? editingSequence + 1 : nextSequence + 1;
      
      setMessages(prev => [...prev, { 
        id: assistantMessageId, 
        role: 'assistant', 
        content: '',
        sequence: assistantSequence,
        chat_id: chatId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }]);
      
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
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: assistantMessage } 
                  : msg
              ));
            }
          }
        }
      }
      
      // Clear selected files after successful submission
      setSelectedFiles([]);
      
      // Reset editing state if applicable
      if (editingSequence !== null) {
        setEditingMessageId(null);
        setEditingSequence(null);
      }
      
      // Fetch the updated messages to get proper attachments and IDs
      const updatedChat = await chatApi.getChat(chatId);
      if (updatedChat.messages) {
        setMessages(updatedChat.messages);
      }
      
    } catch (error) {
      console.error('Error in message submission:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const startEditMessage = (messageId: string) => {
    const message = messages.find(m => m.id === messageId);
    if (message && message.role === 'user') {
      setEditingMessageId(messageId);
      setEditingSequence(message.sequence);
      setInput(message.content);
      setSelectedFiles([]); // Clear selected files when starting edit
    }
  };
  
  const cancelEdit = () => {
    setEditingMessageId(null);
    setEditingSequence(null);
    setInput('');
    setSelectedFiles([]);
  };

  const handleDownloadAttachment = async (attachmentId: string) => {
    try {
      const response = await axios({
        url: `/api/v1/chats/attachments/${attachmentId}/download`,
        method: 'GET',
        responseType: 'blob',
      });
      
      // Create a temporary URL for the file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      
      // Create a link element and trigger download
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'download';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading attachment:', error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Messages area */}
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id} 
              className={`mb-4 ${message.role === 'user' ? 'flex justify-end' : ''}`}
            >
              <div 
                className={`${
                  message.role === 'user' 
                    ? 'bg-primary-500 text-white rounded-l-lg rounded-br-lg' 
                    : 'bg-gray-100 text-gray-800 rounded-r-lg rounded-bl-lg'
                } p-3 max-w-[80%] shadow`}
              >
                {message.role === 'user' && (
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs text-white/80">You</span>
                    <button 
                      onClick={() => startEditMessage(message.id)}
                      className="text-white/80 hover:text-white"
                      title="Edit message"
                    >
                      <FiEdit size={14} />
                    </button>
                  </div>
                )}
                
                {message.role === 'assistant' && (
                  <div className="mb-1">
                    <span className="text-xs text-gray-600">AI Assistant</span>
                  </div>
                )}
                
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                
                {/* Attachments display */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-xs mb-1">
                      {message.role === 'user' ? (
                        <span className="text-white/80">Attachments:</span>
                      ) : (
                        <span className="text-gray-600">Attachments:</span>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {message.attachments.map((attachment) => (
                        <div 
                          key={attachment.id}
                          className={`
                            flex items-center p-1.5 rounded text-xs
                            ${message.role === 'user' 
                              ? 'bg-primary-600 text-white/90' 
                              : 'bg-gray-200 text-gray-800'}
                          `}
                        >
                          <FiFile className="mr-1" size={14} />
                          <span className="truncate max-w-[120px]">
                            {attachment.filename}
                          </span>
                          <div className="flex ml-1">
                            <button
                              onClick={() => handleDownloadAttachment(attachment.id)}
                              className={`p-0.5 rounded-full ${
                                message.role === 'user' ? 'hover:bg-primary-700' : 'hover:bg-gray-300'
                              }`}
                              title="Download"
                            >
                              <FiDownload size={12} />
                            </button>
                            
                            {/* Delete button only for user messages being edited */}
                            {message.role === 'user' && editingMessageId === message.id && (
                              <button
                                onClick={() => handleDeleteAttachment(attachment.id, message.id)}
                                className="p-0.5 rounded-full hover:bg-primary-700 ml-1"
                                title="Delete attachment"
                              >
                                <FiX size={12} />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {isLoading && message === messages[messages.length - 1] && message.role === 'user' && (
                  <div className="mt-2 flex items-center">
                    <div className="loading-dots flex space-x-1">
                      <div className="h-2 w-2 bg-white rounded-full animate-bounce"></div>
                      <div className="h-2 w-2 bg-white rounded-full animate-bounce delay-75"></div>
                      <div className="h-2 w-2 bg-white rounded-full animate-bounce delay-150"></div>
                    </div>
                    <span className="ml-2 text-sm text-white/80">AI is thinking...</span>
                  </div>
                )}
                
                {editedMessageIds.has(message.id) && (
                  <div className="text-xs mt-1 text-right">
                    <span className={`${message.role === 'user' ? 'text-white/80' : 'text-gray-600'} font-medium px-1.5 py-0.5 rounded-full border ${message.role === 'user' ? 'border-white/30' : 'border-gray-300'}`}>
                      edited
                    </span>
                  </div>
                )}
                
                {/* Add attachment button when editing this message */}
                {message.role === 'user' && editingMessageId === message.id && (
                  <div className="mt-2 pt-2 border-t border-white/20">
                    <button
                      type="button"
                      onClick={handleSelectFilesClick}
                      className="flex items-center text-white/80 hover:text-white text-xs py-1"
                      title="Add attachment"
                    >
                      <FiPaperclip size={12} className="mr-1" />
                      Add attachment
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Selected files display - only show when editing or creating new message */}
      {selectedFiles.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-200">
          <div className="text-sm font-medium mb-1 text-gray-700">
            Selected files to upload:
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm">
                <FiFile className="mr-1" size={14} />
                <span className="truncate max-w-[150px]">{file.name}</span>
                <button 
                  onClick={() => removeFile(index)}
                  className="ml-1 text-gray-500 hover:text-gray-700"
                >
                  <FiX size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Message input */}
      <div className="border-t border-gray-200 p-4">
        <form 
          onSubmit={handleSubmit}
          className="flex flex-col"
        >
          {editingMessageId && (
            <div className={`mb-2 p-2 ${selectedFiles.length > 0 ? 'bg-yellow-50' : 'bg-gray-50'} border ${selectedFiles.length > 0 ? 'border-yellow-300' : 'border-gray-200'} rounded-lg`}>
              <div className="text-sm font-medium mb-1 text-gray-700 flex items-center">
                <FiEdit className="mr-1" size={14} />
                Editing message {selectedFiles.length > 0 && " (adding new attachments)"}
              </div>
            </div>
          )}
          <div className="flex items-center">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={editingMessageId ? "Edit your message..." : "Type your message..."}
              className={`flex-1 border ${editingMessageId ? (selectedFiles.length > 0 ? 'border-yellow-400' : 'border-yellow-300') : 'border-gray-300'} rounded-l-lg py-2 px-4 focus:outline-none focus:ring-2 ${editingMessageId ? 'focus:ring-yellow-400' : 'focus:ring-primary-500'}`}
            />
            <button
              type="button"
              onClick={handleSelectFilesClick}
              className={`${editingMessageId ? (selectedFiles.length > 0 ? 'bg-yellow-100 hover:bg-yellow-200' : 'bg-gray-100 hover:bg-gray-200') : 'bg-gray-100 hover:bg-gray-200'} text-gray-700 px-3 py-2.5 focus:outline-none`}
              title="Attach files"
            >
              <FiPaperclip size={20} />
            </button>
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
              className={`${editingMessageId ? (selectedFiles.length > 0 ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-yellow-400 hover:bg-yellow-500') : 'bg-primary-500 hover:bg-primary-600'} text-white rounded-r-lg p-2.5 focus:outline-none focus:ring-2 ${editingMessageId ? 'focus:ring-yellow-400' : 'focus:ring-primary-500'}`}
            >
              <FiSend size={20} />
            </button>
          </div>
          
          {/* Hidden file input */}
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
            multiple
          />
        </form>
      </div>
    </div>
  );
};

export default ChatUI; 