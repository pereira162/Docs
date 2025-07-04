# Frontend Next.js - Sistema RAG

## Estrutura do Projeto Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── documents/
│   │   ├── categories/
│   │   └── settings/
│   ├── components/
│   │   ├── ui/
│   │   ├── forms/
│   │   ├── navigation/
│   │   ├── charts/
│   │   └── document/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── utils.ts
│   │   └── validations.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useDocuments.ts
│   │   └── useRAG.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── documentStore.ts
│   │   └── uiStore.ts
│   └── types/
│       ├── api.ts
│       ├── document.ts
│       └── user.ts
├── components.json
├── next.config.js
├── tailwind.config.js
└── package.json
```

## 1. Configuração Base

### next.config.js
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig
```

### tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 2. Tipos TypeScript

### src/types/api.ts
```typescript
export interface APIResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ProcessingStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  step?: string;
  error_message?: string;
}
```

### src/types/document.ts
```typescript
export interface DocumentLink {
  id: string;
  url: string;
  title?: string;
  description?: string;
  category_id?: string;
  status: ProcessingStatus['status'];
  file_type?: string;
  file_size?: number;
  processed_at?: string;
  error_message?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  color?: string;
  created_at: string;
}

export interface ProcessedDocument {
  id: string;
  document_link_id: string;
  text_content: string;
  chunk_count: number;
  processing_time_ms: number;
  docling_metadata?: Record<string, any>;
  created_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  metadata?: Record<string, any>;
}

export interface RAGQuery {
  query: string;
  max_results?: number;
  threshold?: number;
  category_filter?: string[];
}

export interface RAGResult {
  id: string;
  content: string;
  score: number;
  document_title?: string;
  document_url?: string;
  chunk_index: number;
}

export interface RAGResponse {
  query: string;
  results: RAGResult[];
  total_results: number;
  processing_time: number;
}
```

## 3. Cliente API

### src/lib/api.ts
```typescript
import { APIResponse, PaginatedResponse } from '@/types/api';
import { DocumentLink, Category, RAGQuery, RAGResponse } from '@/types/document';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

class APIClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    
    // Recuperar token do localStorage no cliente
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.detail || data.message || 'Erro na requisição',
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Erro desconhecido',
      };
    }
  }

  // Auth
  async login(email: string, password: string) {
    return this.request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email: string, password: string, name: string) {
    return this.request<{ message: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
  }

  // Document Links
  async getDocumentLinks(page = 1, per_page = 20) {
    return this.request<PaginatedResponse<DocumentLink>>(
      `/api/v1/links?page=${page}&per_page=${per_page}`
    );
  }

  async createDocumentLink(data: Partial<DocumentLink>) {
    return this.request<DocumentLink>('/api/v1/links', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateDocumentLink(id: string, data: Partial<DocumentLink>) {
    return this.request<DocumentLink>(`/api/v1/links/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteDocumentLink(id: string) {
    return this.request<{ message: string }>(`/api/v1/links/${id}`, {
      method: 'DELETE',
    });
  }

  async processDocumentLink(id: string) {
    return this.request<{ task_id: string }>(`/api/v1/links/${id}/process`, {
      method: 'POST',
    });
  }

  // Categories
  async getCategories() {
    return this.request<Category[]>('/api/v1/categories');
  }

  async createCategory(data: Partial<Category>) {
    return this.request<Category>('/api/v1/categories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // RAG
  async queryRAG(query: RAGQuery) {
    return this.request<RAGResponse>('/api/v1/rag/query', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async searchDocuments(query: string, limit = 10) {
    return this.request<RAGResult[]>('/api/v1/rag/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  // Stats
  async getStats() {
    return this.request<{
      total_documents: number;
      processed_documents: number;
      total_chunks: number;
      processing_queue: number;
    }>('/api/v1/stats');
  }
}

export const apiClient = new APIClient(API_BASE_URL!);
```

## 4. Hooks Customizados

### src/hooks/useDocuments.ts
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { DocumentLink } from '@/types/document';
import { toast } from 'sonner';

export function useDocuments(page = 1, per_page = 20) {
  return useQuery({
    queryKey: ['documents', page, per_page],
    queryFn: () => apiClient.getDocumentLinks(page, per_page),
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<DocumentLink>) => apiClient.createDocumentLink(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Documento adicionado com sucesso!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Erro ao adicionar documento');
    },
  });
}

export function useProcessDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.processDocumentLink(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Processamento iniciado!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Erro ao iniciar processamento');
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteDocumentLink(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      toast.success('Documento removido com sucesso!');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Erro ao remover documento');
    },
  });
}
```

### src/hooks/useRAG.ts
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { RAGQuery } from '@/types/document';

export function useRAGQuery() {
  return useMutation({
    mutationFn: (query: RAGQuery) => apiClient.queryRAG(query),
  });
}

export function useSearchDocuments() {
  return useMutation({
    mutationFn: ({ query, limit }: { query: string; limit?: number }) =>
      apiClient.searchDocuments(query, limit),
  });
}
```

## 5. Componentes UI Principais

### src/components/document/DocumentList.tsx
```typescript
'use client';

import { useState } from 'react';
import { useDocuments, useDeleteDocument, useProcessDocument } from '@/hooks/useDocuments';
import { DocumentLink } from '@/types/document';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, ExternalLink, Play, Trash } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface DocumentListProps {
  searchQuery?: string;
  categoryFilter?: string;
}

export function DocumentList({ searchQuery, categoryFilter }: DocumentListProps) {
  const [page, setPage] = useState(1);
  const { data: documentsResponse, isLoading } = useDocuments(page);
  const deleteDocument = useDeleteDocument();
  const processDocument = useProcessDocument();

  const documents = documentsResponse?.data?.items || [];

  const getStatusColor = (status: DocumentLink['status']) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: DocumentLink['status']) => {
    switch (status) {
      case 'completed': return 'Concluído';
      case 'processing': return 'Processando';
      case 'failed': return 'Erro';
      default: return 'Pendente';
    }
  };

  if (isLoading) {
    return <div className="flex justify-center p-8">Carregando documentos...</div>;
  }

  return (
    <div className="space-y-4">
      {documents.map((document) => (
        <Card key={document.id}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <CardTitle className="text-lg">
                  {document.title || 'Documento sem título'}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {document.description}
                </p>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => window.open(document.url, '_blank')}
                  >
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Abrir Link
                  </DropdownMenuItem>
                  {document.status === 'pending' && (
                    <DropdownMenuItem
                      onClick={() => processDocument.mutate(document.id)}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Processar
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    onClick={() => deleteDocument.mutate(document.id)}
                    className="text-red-600"
                  >
                    <Trash className="mr-2 h-4 w-4" />
                    Remover
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardHeader>
          
          <CardContent>
            <div className="flex items-center space-x-4 text-sm text-muted-foreground">
              <Badge className={getStatusColor(document.status)}>
                {getStatusText(document.status)}
              </Badge>
              
              {document.file_type && (
                <span>Tipo: {document.file_type.toUpperCase()}</span>
              )}
              
              {document.file_size && (
                <span>
                  Tamanho: {(document.file_size / 1024 / 1024).toFixed(2)} MB
                </span>
              )}
            </div>
            
            {document.error_message && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                {document.error_message}
              </div>
            )}
          </CardContent>
          
          <CardFooter className="text-xs text-muted-foreground">
            Adicionado {formatDistanceToNow(new Date(document.created_at), { 
              addSuffix: true, 
              locale: ptBR 
            })}
            {document.processed_at && (
              <span className="ml-4">
                Processado {formatDistanceToNow(new Date(document.processed_at), { 
                  addSuffix: true, 
                  locale: ptBR 
                })}
              </span>
            )}
          </CardFooter>
        </Card>
      ))}
      
      {documents.length === 0 && (
        <div className="text-center p-8 text-muted-foreground">
          Nenhum documento encontrado
        </div>
      )}
    </div>
  );
}
```

### src/components/forms/AddDocumentForm.tsx
```typescript
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateDocument } from '@/hooks/useDocuments';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const formSchema = z.object({
  url: z.string().url('URL inválida'),
  title: z.string().optional(),
  description: z.string().optional(),
  category_id: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

interface AddDocumentFormProps {
  onSuccess?: () => void;
  categories?: Array<{ id: string; name: string }>;
}

export function AddDocumentForm({ onSuccess, categories = [] }: AddDocumentFormProps) {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      url: '',
      title: '',
      description: '',
      category_id: '',
    },
  });

  const createDocument = useCreateDocument();

  const onSubmit = async (data: FormData) => {
    const result = await createDocument.mutateAsync(data);
    
    if (result.success) {
      form.reset();
      onSuccess?.();
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL do Documento *</FormLabel>
              <FormControl>
                <Input 
                  placeholder="https://exemplo.com/documento.pdf" 
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Título</FormLabel>
              <FormControl>
                <Input 
                  placeholder="Título do documento (opcional)" 
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descrição</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="Descrição do documento (opcional)" 
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {categories.length > 0 && (
          <FormField
            control={form.control}
            name="category_id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Categoria</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione uma categoria" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {categories.map((category) => (
                      <SelectItem key={category.id} value={category.id}>
                        {category.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        )}

        <Button 
          type="submit" 
          className="w-full"
          disabled={createDocument.isPending}
        >
          {createDocument.isPending ? 'Adicionando...' : 'Adicionar Documento'}
        </Button>
      </form>
    </Form>
  );
}
```

## 6. Páginas Principais

### src/app/dashboard/page.tsx
```typescript
import { Suspense } from 'react';
import { DocumentList } from '@/components/document/DocumentList';
import { AddDocumentForm } from '@/components/forms/AddDocumentForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function DashboardPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard RAG</h1>
      </div>

      <Tabs defaultValue="documents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="documents">Documentos</TabsTrigger>
          <TabsTrigger value="add">Adicionar</TabsTrigger>
          <TabsTrigger value="search">Buscar</TabsTrigger>
        </TabsList>

        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <CardTitle>Documentos</CardTitle>
            </CardHeader>
            <CardContent>
              <Suspense fallback={<div>Carregando...</div>}>
                <DocumentList />
              </Suspense>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="add">
          <Card>
            <CardHeader>
              <CardTitle>Adicionar Documento</CardTitle>
            </CardHeader>
            <CardContent>
              <AddDocumentForm />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="search">
          <Card>
            <CardHeader>
              <CardTitle>Busca RAG</CardTitle>
            </CardHeader>
            <CardContent>
              {/* Componente de busca RAG será implementado */}
              <div className="text-center p-8 text-muted-foreground">
                Funcionalidade de busca em desenvolvimento
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

Esta estrutura frontend fornece uma base sólida para o sistema RAG com interface moderna, responsiva e funcional.
