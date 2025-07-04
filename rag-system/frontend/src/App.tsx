import React, { useState, useEffect } from 'react';
import './App.css';

interface RAGResult {
  content: string;
  score: number;
  source_url: string;
  title?: string;
}

interface DocumentAdd {
  url: string;
  title?: string;
}

interface Stats {
  vectors_count: number;
  indexed_vectors: number;
  status: string;
  collection_name: string;
}

// Alterar para URL do Railway após deploy
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [password, setPassword] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [newDoc, setNewDoc] = useState<DocumentAdd>({ url: '', title: '' });
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<RAGResult[]>([]);
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
        setPassword(testPassword);
        localStorage.setItem('rag_password', testPassword);
        loadStats();
      }
    } catch (error) {
      console.log('Erro na autenticação automática');
    }
  };

  const authenticate = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`, {
        headers: {
          'Authorization': `Bearer ${password}`
        }
      });

      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('rag_password', password);
        setMessage('Autenticado com sucesso!');
        loadStats();
      } else {
        setMessage('Senha incorreta!');
      }
    } catch (error) {
      setMessage('Erro de conexão com o servidor');
    }
  };

  const logout = () => {
    setIsAuthenticated(false);
    setPassword('');
    localStorage.removeItem('rag_password');
    setStats(null);
    setResults([]);
    setMessage('');
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`, {
        headers: {
          'Authorization': `Bearer ${password}`
        }
      });

      if (response.ok) {
        const statsData = await response.json();
        setStats(statsData);
      }
    } catch (error) {
      console.log('Erro ao carregar estatísticas');
    }
  };

  const addDocument = async () => {
    if (!newDoc.url) return;
    
    setLoading(true);
    setMessage('Processando documento...');
    
    try {
      const response = await fetch(`${API_BASE}/add-document`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify(newDoc)
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`✅ Documento adicionado: ${result.chunks_created} chunks criados`);
        setNewDoc({ url: '', title: '' });
        loadStats(); // Atualizar estatísticas
      } else {
        const error = await response.json();
        setMessage(`❌ Erro: ${error.detail}`);
      }
    } catch (error) {
      setMessage('❌ Erro de conexão');
    }
    setLoading(false);
  };

  const searchDocuments = async () => {
    if (!query) return;
    
    setLoading(true);
    setMessage('Buscando...');
    
    try {
      const response = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${password}`
        },
        body: JSON.stringify({ query, max_results: 5 })
      });

      if (response.ok) {
        const searchResults = await response.json();
        setResults(searchResults);
        setMessage(`🔍 ${searchResults.length} resultados encontrados`);
      } else {
        const error = await response.json();
        setMessage(`❌ Erro na busca: ${error.detail}`);
      }
    } catch (error) {
      setMessage('❌ Erro de conexão');
    }
    setLoading(false);
  };

  const clearDocuments = async () => {
    if (!confirm('⚠️ Isso irá apagar todos os documentos. Continuar?')) return;
    
    setLoading(true);
    setMessage('Limpando documentos...');
    
    try {
      const response = await fetch(`${API_BASE}/clear`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${password}`
        }
      });

      if (response.ok) {
        setMessage('🗑️ Todos os documentos foram removidos');
        setResults([]);
        loadStats();
      } else {
        setMessage('❌ Erro ao limpar documentos');
      }
    } catch (error) {
      setMessage('❌ Erro de conexão');
    }
    setLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">🤖 RAG System</h1>
            <p className="text-gray-600">Sistema de Documentação Inteligente</p>
          </div>
          
          <div className="space-y-4">
            <input
              type="password"
              placeholder="Senha de acesso"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && authenticate()}
            />
            <button
              onClick={authenticate}
              className="w-full bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
            >
              🔐 Entrar
            </button>
          </div>
          
          {message && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {message}
            </div>
          )}
          
          <div className="mt-6 text-xs text-gray-500 text-center">
            <p>MVP - Sistema RAG Gratuito</p>
            <p>Processa documentos e responde perguntas</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">🤖 Sistema RAG</h1>
            <p className="text-gray-600 text-sm">Documentação Inteligente</p>
          </div>
          
          <div className="flex items-center space-x-4">
            {stats && (
              <div className="text-sm text-gray-600">
                📊 {stats.vectors_count} documentos
              </div>
            )}
            <button
              onClick={logout}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors text-sm"
            >
              🚪 Sair
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-4 space-y-6">
        
        {/* Mensagem de Status */}
        {message && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg">
            {message}
          </div>
        )}

        {/* Estatísticas */}
        {stats && (
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <h3 className="font-medium text-gray-800 mb-2">📈 Estatísticas do Sistema</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Documentos:</span>
                <span className="ml-1 font-medium">{stats.vectors_count}</span>
              </div>
              <div>
                <span className="text-gray-600">Indexados:</span>
                <span className="ml-1 font-medium">{stats.indexed_vectors}</span>
              </div>
              <div>
                <span className="text-gray-600">Status:</span>
                <span className="ml-1 font-medium">{stats.status}</span>
              </div>
              <div>
                <span className="text-gray-600">Coleção:</span>
                <span className="ml-1 font-medium">{stats.collection_name}</span>
              </div>
            </div>
          </div>
        )}

        {/* Adicionar Documento */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">📄 Adicionar Documento</h2>
            {stats && stats.vectors_count > 0 && (
              <button
                onClick={clearDocuments}
                disabled={loading}
                className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 disabled:bg-gray-400"
              >
                🗑️ Limpar Tudo
              </button>
            )}
          </div>
          
          <div className="space-y-3">
            <input
              type="url"
              placeholder="🔗 URL do documento (PDF, HTML, artigo, etc.)"
              value={newDoc.url}
              onChange={(e) => setNewDoc({ ...newDoc, url: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <input
              type="text"
              placeholder="📝 Título (opcional)"
              value={newDoc.title}
              onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={addDocument}
              disabled={loading || !newDoc.url}
              className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 disabled:bg-gray-400 transition-colors font-medium"
            >
              {loading ? '⏳ Processando...' : '➕ Adicionar Documento'}
            </button>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p>💡 <strong>Dica:</strong> Suporta links de artigos, PDFs, documentação, etc.</p>
          </div>
        </div>

        {/* Busca RAG */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">🔍 Consulta Inteligente</h2>
          <div className="flex space-x-3">
            <input
              type="text"
              placeholder="💭 Faça uma pergunta sobre os documentos..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
            />
            <button
              onClick={searchDocuments}
              disabled={loading || !query}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 transition-colors font-medium"
            >
              {loading ? '⏳' : '🔍'} Buscar
            </button>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p>💡 <strong>Exemplos:</strong> "Como configurar X?", "O que é Y?", "Resumo sobre Z"</p>
          </div>
        </div>

        {/* Resultados */}
        {results.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              📋 Resultados ({results.length})
            </h2>
            <div className="space-y-4">
              {results.map((result, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 bg-gray-50 p-4 rounded-r-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900 text-lg">
                      📄 {result.title || 'Documento'}
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500 bg-white px-2 py-1 rounded">
                        📊 {result.score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-3 leading-relaxed">
                    {result.content}
                  </p>
                  
                  <a
                    href={result.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    🔗 Ver fonte original →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Guia de Uso */}
        {(!stats || stats.vectors_count === 0) && (
          <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg">
            <h3 className="font-medium text-yellow-800 mb-3">🚀 Como começar:</h3>
            <ol className="list-decimal list-inside space-y-2 text-yellow-700 text-sm">
              <li>Adicione documentos usando URLs de artigos, PDFs ou páginas web</li>
              <li>Aguarde o processamento (alguns segundos)</li>
              <li>Faça perguntas sobre o conteúdo dos documentos</li>
              <li>Receba respostas baseadas nos documentos adicionados</li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
