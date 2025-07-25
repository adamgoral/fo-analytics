import { apiClient } from './api';

export interface DocumentResponse {
  id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  processed_at?: string;
  extracted_text?: string;
  strategies_count: number;
  user_id: string;
  user?: {
    id: string;
    email: string;
    full_name?: string;
  };
}

export interface DocumentContent {
  text: string;
  metadata: {
    pages?: number;
    created_at?: string;
    file_type?: string;
  };
  page_contents?: Array<{
    page_number: number;
    text: string;
  }>;
}

export interface ExtractedStrategy {
  id: string;
  name: string;
  description: string;
  asset_class: string;
  timeframe: string;
  risk_level: string;
  entry_conditions: string[];
  exit_conditions: string[];
  risk_management: Record<string, any>;
  performance_metrics?: {
    expected_return?: number;
    sharpe_ratio?: number;
    max_drawdown?: number;
  };
  confidence_score: number;
  extracted_at: string;
  document_id: string;
}

export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  skip: number;
  limit: number;
}

export const documentsApi = {
  // Get all documents
  list: () => apiClient.get<DocumentListResponse>('/documents'),

  // Get single document
  get: (id: string) => apiClient.get<DocumentResponse>(`/documents/${id}`),

  // Upload document
  upload: (file: File, onProgress?: (progress: number) => void) =>
    apiClient.uploadFile<DocumentResponse>('/documents/upload', file, onProgress),

  // Delete document
  delete: (id: string) => apiClient.delete(`/documents/${id}`),

  // Process document (trigger re-analysis)
  process: (id: string) => apiClient.post(`/documents/${id}/process`),

  // Get document content
  getContent: (id: string, page?: number) => {
    const params = page ? `?page=${page}` : '';
    return apiClient.get<DocumentContent>(`/documents/${id}/content${params}`);
  },

  // Get document strategies
  getStrategies: (id: string) => 
    apiClient.get<ExtractedStrategy[]>(`/documents/${id}/strategies`),

  // Download document
  download: async (id: string, fileName: string) => {
    const response = await apiClient.get(`/documents/${id}/download`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response as BlobPart]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};