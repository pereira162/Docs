import React, { useState, useEffect } from 'react';
import './App.css';

interface DocumentResult {
  content: string;
  score: number;
  metadata: {
    source_url?: string;
    source_file?: string;
    title?: string;
    document_id?: string;
    chunk_index?: number;
    page_count?: number;
    processing_time?: number;
    file_size?: number;
  };
}

interface QueryResponse {
  query: string;
  answer: string;
  sources: DocumentResult[];
}

interface DocumentAdd {
  url: string;
  title?: string;
}

interface Stats {
  vector_storage: {
    total_chunks: number;
    collection_name: string;
    storage_path: string;
  };
  documents: {
    count: number;
    total_size_mb: number;
  };
  system: {
    data_path: string;
    models_path: string;
    gemini_configured: boolean;
  };
}

// API base URL - local development
const API_BASE = 'http://localhost:8000';

function App() {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [newDoc, setNewDoc] = useState<DocumentAdd>({ url: '', title: '' });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileTitle, setFileTitle] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<DocumentResult[]>([]);
  const [aiAnswer, setAiAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    // Verificar se já está autenticado
    const savedPassword = localStorage.getItem('rag_password');
    if (savedPassword) {
      setPassword(savedPassword);
      testAuthentication(savedPassword);
    }
  }, []);

  const testAuthentication = async (testPassword: string) => {
    try {
      const response = await fetch(`${API_BASE}/health`, {
        headers: {
          'Authorization': `Bearer ${testPassword}`
        }
      });

      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('rag_password', testPassword);
        loadStats();
      }
    } catch (error) {
      console.error('Erro na autenticação:', error);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    await testAuthentication(password);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setPassword('');
    localStorage.removeItem('rag_password');
    setStats(null);
    setResults([]);
    setAiAnswer('');
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`, {
        headers: {
          'Authorization': `Bearer ${password}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const addDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDoc.url.trim()) return;

    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`${API_BASE}/add-document`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify(newDoc)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ Documento adicionado com sucesso! ${data.chunks_created} chunks criados em ${data.processing_time}s`);
        setNewDoc({ url: '', title: '' });
        loadStats();
      } else {
        setMessage(`❌ Erro: ${data.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    }

    setLoading(false);
  };

  const uploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setMessage('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (fileTitle.trim()) {
        formData.append('title', fileTitle);
      }

      const response = await fetch(`${API_BASE}/upload-document`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${password}`
        },
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ Arquivo enviado com sucesso! ${data.chunks_created} chunks criados em ${data.processing_time}s`);
        setSelectedFile(null);
        setFileTitle('');
        loadStats();
      } else {
        setMessage(`❌ Erro: ${data.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    }

    setLoading(false);
  };

  const searchDocuments = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResults([]);
    setAiAnswer('');

    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify({ 
          query: query,
          max_results: 5 
        })
      });

      const data: QueryResponse = await response.json();

      if (response.ok) {
        setResults(data.sources);
        setAiAnswer(data.answer);
      } else {
        setMessage(`❌ Erro na busca: ${data}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    }

    setLoading(false);
  };

  const clearAllData = async () => {
    if (!confirm('Tem certeza que deseja limpar todos os dados? Esta ação é irreversível.')) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/clear`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${password}`
        }
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('✅ Todos os dados foram limpos!');
        setResults([]);
        setAiAnswer('');
        loadStats();
      } else {
        setMessage(`❌ Erro: ${data.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Erro: ${error}`);
    }

    setLoading(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🚀 RAG Docling System
            </h1>
            <p className="text-gray-600">
              Sistema RAG com suporte a arquivos grandes
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Senha de Acesso
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Digite a senha"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Entrar
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>✨ Processamento de arquivos até 100MB+</p>
            <p>🗄️ Armazenamento local ilimitado</p>
            <p>🤖 IA Gemini integrada</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                🚀 RAG Docling System
              </h1>
              {stats && (
                <span className="ml-4 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  📊 {stats.documents.count} documentos ({stats.documents.total_size_mb} MB)
                </span>
              )}
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status e Estatísticas */}
        {stats && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">📈 Estatísticas do Sistema</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-blue-600 font-medium">Total de Chunks</div>
                <div className="text-2xl font-bold text-blue-900">{stats.vector_storage.total_chunks}</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm text-green-600 font-medium">Documentos</div>
                <div className="text-2xl font-bold text-green-900">{stats.documents.count}</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm text-purple-600 font-medium">Tamanho Total</div>
                <div className="text-2xl font-bold text-purple-900">{stats.documents.total_size_mb} MB</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-sm text-yellow-600 font-medium">IA Gemini</div>
                <div className="text-2xl font-bold text-yellow-900">
                  {stats.system.gemini_configured ? '✅' : '❌'}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Adicionar Documentos */}
          <div className="space-y-6">
            {/* Por URL */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">🌐 Adicionar por URL</h2>
              <form onSubmit={addDocument} className="space-y-4">
                <div>
                  <input
                    type="url"
                    value={newDoc.url}
                    onChange={(e) => setNewDoc({...newDoc, url: e.target.value})}
                    placeholder="https://exemplo.com/documento.pdf"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="text"
                    value={newDoc.title}
                    onChange={(e) => setNewDoc({...newDoc, title: e.target.value})}
                    placeholder="Título do documento (opcional)"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium"
                >
                  {loading ? '⏳ Processando...' : '📄 Adicionar Documento'}
                </button>
              </form>
            </div>

            {/* Upload de Arquivo */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">📁 Upload de Arquivo</h2>
              <form onSubmit={uploadDocument} className="space-y-4">
                <div>
                  <input
                    type="file"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    accept=".pdf,.docx,.txt,.md"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Suporte: PDF, DOCX, TXT, MD (até 100MB+)
                  </p>
                </div>
                <div>
                  <input
                    type="text"
                    value={fileTitle}
                    onChange={(e) => setFileTitle(e.target.value)}
                    placeholder="Título do documento (opcional)"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !selectedFile}
                  className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-medium"
                >
                  {loading ? '⏳ Enviando...' : '🚀 Upload Documento'}
                </button>
              </form>
            </div>

            {/* Controles */}
            {stats && stats.documents.count > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Controles</h2>
                <button
                  onClick={clearAllData}
                  disabled={loading}
                  className="w-full bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors font-medium"
                >
                  🗑️ Limpar Todos os Dados
                </button>
              </div>
            )}
          </div>

          {/* Busca e Resultados */}
          <div className="space-y-6">
            {/* Busca */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">🔍 Buscar nos Documentos</h2>
              <form onSubmit={searchDocuments} className="space-y-4">
                <div>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Digite sua pergunta ou termo de busca..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors font-medium"
                >
                  {loading ? '🔍 Buscando...' : '🤖 Buscar com IA'}
                </button>
              </form>
            </div>

            {/* Resposta da IA */}
            {aiAnswer && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">🤖 Resposta da IA</h2>
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                  <p className="text-gray-800 whitespace-pre-wrap">{aiAnswer}</p>
                </div>
              </div>
            )}

            {/* Resultados */}
            {results.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  📚 Documentos Encontrados ({results.length})
                </h2>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {results.map((result, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-medium text-gray-900">
                          📄 {result.metadata.title || result.metadata.source_file || 'Documento'}
                        </h3>
                        <span className="text-sm font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                          {Math.round(result.score * 100)}% match
                        </span>
                      </div>
                      <p className="text-gray-700 text-sm mb-3 line-clamp-3">
                        {result.content.substring(0, 200)}...
                      </p>
                      <div className="text-xs text-gray-500 space-y-1">
                        {result.metadata.source_url && (
                          <div>
                            🔗 <a 
                              href={result.metadata.source_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              {result.metadata.source_url}
                            </a>
                          </div>
                        )}
                        {result.metadata.file_size && (
                          <div>📏 Tamanho: {formatFileSize(result.metadata.file_size)}</div>
                        )}
                        {result.metadata.page_count && (
                          <div>📄 Páginas: {result.metadata.page_count}</div>
                        )}
                        <div>🧩 Chunk {result.metadata.chunk_index || 0}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Empty State */}
        {(!stats || stats.documents.count === 0) && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Comece adicionando documentos
            </h2>
            <p className="text-gray-600 max-w-md mx-auto">
              Adicione documentos por URL ou upload para começar a usar o sistema RAG.
              Suporte a arquivos de até 100MB+ com processamento Docling.
            </p>
          </div>
        )}

        {/* Mensagens */}
        {message && (
          <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50">
            <p className="text-sm">{message}</p>
            <button
              onClick={() => setMessage('')}
              className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
