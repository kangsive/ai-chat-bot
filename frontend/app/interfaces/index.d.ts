// Type declarations for chat interfaces
declare module '../interfaces/chat' {
  export interface Attachment {
    id: string;
    filename: string;
    file_type: string;
    file_size: number;
    file_path?: string;
    message_id: string;
    created_at: string;
    updated_at: string;
  }

  export interface Message {
    id: string;
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string;
    reasoning_content?: string;
    sequence: number;
    tokens?: number;
    message_metadata?: any;
    chat_id: string;
    created_at: string;
    updated_at: string;
    attachments?: Attachment[];
  }

  export interface Chat {
    id: string;
    title?: string;
    model?: string;
    is_archived: boolean;
    user_id: string;
    created_at: string;
    updated_at: string;
    messages: Message[];
  }

  export interface ChatList {
    chats: Chat[];
  }
} 