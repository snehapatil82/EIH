import { apiClient } from './api';
import { Conversation, ChatAnswerResponse } from '../types/chat';

export const chatService = {
  async askQuestion(repoId: string, question: string, conversationId?: string): Promise<ChatAnswerResponse> {
    const res = await apiClient.post<ChatAnswerResponse>(`/repositories/${repoId}/ask`, {
      question,
      conversation_id: conversationId,
    });
    return res.data;
  },

  async listConversations(repoId: string): Promise<Conversation[]> {
    const res = await apiClient.get<Conversation[]>(`/repositories/${repoId}/conversations`);
    return res.data;
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const res = await apiClient.get<Conversation>(`/conversations/${conversationId}`);
    return res.data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/conversations/${conversationId}`);
  },
};
