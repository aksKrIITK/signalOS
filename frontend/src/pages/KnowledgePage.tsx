import React, { useState } from 'react';
import {
  BookOpen,
  Plus,
  Search,
  Upload,
  Layers,
  Sparkles,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { api } from '../lib/api';

export const KnowledgePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  // New Document Modal
  const [showUpload, setShowUpload] = useState(false);
  const [title, setTitle] = useState('SignalOS Enterprise Battlecard 2026');
  const [content, setContent] = useState(
    'SignalOS empowers modern GTM teams with deterministic LangGraph execution, strict SSRF safety, hybrid scoring, and multi-tenant pgvector RAG retrieval to generate hyper-personalized cold outreach with human approval.'
  );

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;
    setSearching(true);
    try {
      const data = await api.searchKnowledge(query, 3);
      setResults(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.uploadDocument(title, content);
      alert('Document chunked and stored in pgvector successfully!');
      setShowUpload(false);
    } catch (e) {
      alert('Error uploading document');
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <BookOpen className="w-6 h-6 text-brand-cyan" />
            RAG Knowledge Base & pgvector
          </h2>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Store product battlecards, sales playbooks, and query with HNSW cosine similarity search
          </p>
        </div>

        <button
          onClick={() => setShowUpload(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-indigo text-dark-900 font-bold text-xs font-mono flex items-center gap-2 hover:opacity-95 transition-all shadow-glow-cyan"
        >
          <Plus className="w-4 h-4" />
          Ingest Knowledge Document
        </button>
      </div>

      {/* Semantic Vector Search Testing Panel */}
      <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Sparkles className="w-4 h-4 text-brand-cyan" />
          Test Multi-Tenant Vector Search
        </div>

        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query (e.g. 'objection handling for security compliance')..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl glass-input text-xs font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-5 py-2.5 rounded-xl bg-dark-700 hover:bg-dark-600 text-brand-cyan font-mono text-xs font-bold border border-brand-cyan/30"
          >
            {searching ? 'Vector Searching...' : 'Vector Query'}
          </button>
        </form>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-3 pt-3 border-t border-slate-800">
            <div className="text-xs font-mono text-slate-400">
              Retrieved {results.length} Chunks (Cosine Similarity Score &gt; 0.90)
            </div>
            {results.map((r, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-dark-900/60 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-white flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-brand-cyan" />
                    {r.title}
                  </span>
                  <span className="font-mono text-emerald-400 text-[10px] bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    Cosine Similarity: {r.score}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-mono leading-relaxed mt-2">{r.content}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Ingest Modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-2xl rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-dark-800">
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-cyan" />
                Ingest New Knowledge Document
              </h3>
              <button
                onClick={() => setShowUpload(false)}
                className="text-slate-400 hover:text-white text-xs font-mono"
              >
                Cancel
              </button>
            </div>

            <form onSubmit={handleUpload} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Document Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2.5 rounded-xl glass-input text-xs font-semibold text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Document Content</label>
                <textarea
                  rows={6}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full p-3 rounded-xl glass-input text-xs font-mono leading-relaxed"
                  required
                />
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="px-4 py-2 rounded-xl bg-dark-700 text-slate-300 font-mono text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-indigo text-dark-900 font-bold font-mono text-xs shadow-glow-cyan"
                >
                  Chunk, Embed & Store
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
