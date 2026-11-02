import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  MessageSquareCode,
  Send,
  Sparkles,
  Bot,
  User,
  Clock,
  Info,
  Plus,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Search,
  Copy,
  Check,
  MessageSquare,
} from 'lucide-react';
import { Repository } from '../types/repository';
import { Message, Conversation } from '../types/chat';
import { chatService } from '../services/chatService';
import { Button } from '../components/common/Button';
import { Spinner } from '../components/common/Spinner';
import { CitationBadge } from '../components/chat/CitationBadge';

interface ChatPageProps {
  selectedRepo: Repository | null;
}

const SAMPLE_QUESTIONS = [
  'Which database does this project use?',
  'Where is the database connection initialized?',
  'What tables are defined in this project?',
  'How are database migrations handled?',
  'How does authentication work in this repository?',
  'Explain the overall architecture and main entrypoints.',
];

export const ChatPage: React.FC<ChatPageProps> = ({ selectedRepo }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [lastLatency, setLastLatency] = useState<number | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load conversations when repository changes
  useEffect(() => {
    if (!selectedRepo) {
      setConversations([]);
      setActiveConvId(undefined);
      setMessages([]);
      return;
    }
    loadConversations();
  }, [selectedRepo]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const loadConversations = async () => {
    if (!selectedRepo) return;
    try {
      const list = await chatService.listConversations(selectedRepo.id);
      setConversations(list);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const handleSelectConversation = (conv: Conversation) => {
    setActiveConvId(conv.id);
    setMessages(conv.messages || []);
    setLastLatency(null);
  };

  const handleNewChat = () => {
    setActiveConvId(undefined);
    setMessages([]);
    setLastLatency(null);
    setInputQuery('');
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    try {
      await chatService.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleCopyText = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || !selectedRepo || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      citations: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const resp = await chatService.askQuestion(selectedRepo.id, textToSend.trim(), activeConvId);
      setActiveConvId(resp.conversation_id);
      setLastLatency(resp.latency_seconds);

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: resp.answer,
        citations: resp.citations || [],
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      // Refresh sidebar conversation list
      loadConversations();
    } catch (err: any) {
      const errorMessage: Message = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Error generating response: ${err.message || 'Failed to communicate with RAG engine'}`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedRepo) {
    return (
      <div className="p-12 text-center text-slate-400">
        Please select or connect a repository first to ask questions.
      </div>
    );
  }

  const filteredConversations = conversations.filter((c) =>
    (c.title || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  const activeConversation = conversations.find((c) => c.id === activeConvId);

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden bg-slate-950">
      {/* ── Left Sidebar (ChatGPT Style History) ─────────────────────────── */}
      <div
        className={`transition-all duration-300 flex flex-col border-r border-slate-800 bg-slate-900/90 backdrop-blur-md ${
          isSidebarOpen ? 'w-64 sm:w-72' : 'w-0'
        } overflow-hidden flex-shrink-0 z-20`}
      >
        <div className="p-3 border-b border-slate-800/80 flex items-center justify-between gap-2">
          <Button
            variant="primary"
            size="sm"
            className="flex-1 justify-start gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium shadow-md shadow-cyan-900/20"
            onClick={handleNewChat}
          >
            <Plus className="w-4 h-4" />
            <span>New chat</span>
          </Button>

          <button
            onClick={() => setIsSidebarOpen(false)}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            title="Close sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Filter Input */}
        {conversations.length > 5 && (
          <div className="px-3 pt-2.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search chats..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full bg-slate-950/60 border border-slate-800 text-xs rounded-lg pl-8 pr-2 py-1.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60"
              />
            </div>
          </div>
        )}

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1 text-[11px] font-semibold tracking-wider uppercase text-slate-500">
            Recent Conversations
          </div>

          {filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500 leading-relaxed">
              {searchFilter ? 'No matching chats found.' : 'No previous chats yet. Start a new question!'}
            </div>
          ) : (
            filteredConversations.map((c) => {
              const isActive = c.id === activeConvId;
              return (
                <div
                  key={c.id}
                  onClick={() => handleSelectConversation(c)}
                  className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                    isActive
                      ? 'bg-slate-800 text-cyan-300 font-medium border border-cyan-500/30 shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-6">
                    <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                    <span className="truncate">{c.title || 'Untitled conversation'}</span>
                  </div>

                  <button
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-400 rounded transition-all"
                    title="Delete chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="p-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
          <span className="truncate">Repo: {selectedRepo.name}</span>
          <span>{conversations.length} saved</span>
        </div>
      </div>

      {/* ── Main Chat Area ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-slate-950 relative">
        {/* Top Navigation Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/90 bg-slate-900/60 backdrop-blur-md">
          <div className="flex items-center gap-2.5 min-w-0">
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-1.5 text-xs"
                title="Open chat history sidebar"
              >
                <PanelLeft className="w-4 h-4 text-cyan-400" />
                <span className="hidden sm:inline">History</span>
              </button>
            )}

            <div className="flex items-center gap-2 min-w-0">
              <MessageSquareCode className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <h2 className="text-sm font-semibold text-slate-200 truncate">
                {activeConversation?.title || 'New Conversation'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {lastLatency !== null && (
              <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                <Clock className="w-3 h-3 text-cyan-400" />
                <span>{lastLatency}s</span>
              </div>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={handleNewChat}
              className="text-xs h-7 px-2.5 border-slate-700 hover:border-cyan-500/40 text-slate-300"
            >
              <Plus className="w-3.5 h-3.5 mr-1 text-cyan-400" />
              <span>New</span>
            </Button>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-4xl w-full mx-auto">
          {messages.length === 0 ? (
            <div className="my-auto py-12 px-6 text-center space-y-6 glass-card rounded-3xl max-w-2xl mx-auto shadow-2xl relative overflow-hidden">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-950 via-cyan-900 to-blue-900/60 border border-cyan-500/30 flex items-center justify-center mx-auto shadow-lg shadow-cyan-500/20">
                <Sparkles className="w-7 h-7 text-cyan-400" />
              </div>

              <div>
                <h3 className="text-xl font-bold text-slate-100 tracking-tight">
                  Repository Intelligence Assistant
                </h3>
                <p className="text-xs md:text-sm text-slate-400 max-w-md mx-auto mt-2 leading-relaxed">
                  Ask architectural, implementation, or flow questions about{' '}
                  <span className="text-cyan-300 font-semibold">{selectedRepo.name}</span>. Every answer is grounded in verified repository code with line citations.
                </p>
              </div>

              {/* Sample Question Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-left">
                {SAMPLE_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(q)}
                    className="p-3.5 bg-slate-950/80 hover:bg-slate-900 border border-slate-800/80 hover:border-cyan-500/50 rounded-xl text-xs text-slate-300 transition-all text-left group shadow-sm flex items-start gap-2.5 cursor-pointer hover:-translate-y-0.5"
                  >
                    <span className="text-cyan-400 font-mono mt-0.5 font-bold">#</span>
                    <span className="group-hover:text-cyan-200 transition-colors leading-relaxed">
                      {q}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3.5 p-4 md:p-5 rounded-2xl border transition-all animate-fade-in ${
                  msg.role === 'user'
                    ? 'bg-slate-900/90 border-slate-750/90 ml-8 sm:ml-16 shadow-md'
                    : 'glass-card border-slate-800/90 mr-4 sm:mr-12 shadow-xl'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white shadow-cyan-600/30'
                      : 'bg-gradient-to-tr from-purple-600 via-cyan-600 to-blue-600 text-white shadow-cyan-900/40 border border-cyan-400/30'
                  }`}
                >
                  {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className="flex-1 min-w-0 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-500 pb-1.5 border-b border-slate-800/60">
                    <span className="font-semibold text-slate-300">
                      {msg.role === 'user' ? 'You' : 'EIH Intelligence'}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleCopyText(msg.id, msg.content)}
                        className="hover:text-cyan-400 transition-colors p-1 rounded-md hover:bg-slate-800/60"
                        title="Copy to clipboard"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="prose prose-invert prose-xs md:prose-sm max-w-none text-slate-200 leading-relaxed font-sans">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                  </div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2.5 border-t border-slate-800/80">
                      <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Verified Source Citations ({msg.citations.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cit, idx) => (
                          <CitationBadge key={idx} citation={cit} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex items-center gap-3 p-4 glass-card border border-slate-800 rounded-2xl mr-8 shadow-md animate-pulse">
              <Spinner size="md" />
              <span className="text-xs text-slate-300 font-medium">
                Retrieving codebase evidence & synthesizing grounded answer...
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800/90 bg-slate-950/80 backdrop-blur-xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="max-w-4xl mx-auto relative"
          >
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask anything about the codebase (e.g. 'Where is the database connection initialized?')..."
              className="w-full bg-slate-900/90 border border-slate-750/90 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/40 rounded-2xl pl-4 pr-24 py-3.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 shadow-xl transition-all"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isLoading}
            />
            <div className="absolute right-2 top-2">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                className="h-9 px-4 rounded-xl"
                disabled={!inputQuery.trim() || isLoading}
                rightIcon={<Send className="w-3.5 h-3.5" />}
              >
                Send
              </Button>
            </div>
          </form>
          <div className="text-[11px] text-center text-slate-500 mt-2">
            AI-generated answers are grounded in indexed repository code with line citations.
          </div>
        </div>
      </div>
    </div>
  );
};
