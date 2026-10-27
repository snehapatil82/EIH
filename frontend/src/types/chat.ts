export interface Citation {
  file_path: string;
  start_line?: number;
  end_line?: number;
  snippet: string;
  score?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[];
  created_at: string;
}

export interface Conversation {
  id: string;
  repository_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface ChatAnswerResponse {
  conversation_id: string;
  answer: string;
  citations: Citation[];
  latency_seconds: number;
  tokens_used: number;
}
