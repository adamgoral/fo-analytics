import { describe, it, expect, vi, beforeEach } from 'vitest';
import { documentsApi } from '../documents';
import { apiClient } from '../api';

// Mock the apiClient
vi.mock('../api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    uploadFile: vi.fn(),
  },
}));

// Mock window.URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document.createElement and appendChild
const mockLink = {
  href: '',
  setAttribute: vi.fn(),
  click: vi.fn(),
  remove: vi.fn(),
};

document.createElement = vi.fn(() => mockLink as any);
document.body.appendChild = vi.fn();

describe('documentsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should fetch all documents', async () => {
      const mockDocuments = [
        { id: '1', file_name: 'doc1.pdf' },
        { id: '2', file_name: 'doc2.pdf' },
      ];
      vi.mocked(apiClient.get).mockResolvedValue(mockDocuments);

      const result = await documentsApi.list();

      expect(apiClient.get).toHaveBeenCalledWith('/documents');
      expect(result).toEqual(mockDocuments);
    });
  });

  describe('get', () => {
    it('should fetch a single document by id', async () => {
      const mockDocument = { id: '1', file_name: 'doc1.pdf' };
      vi.mocked(apiClient.get).mockResolvedValue(mockDocument);

      const result = await documentsApi.get('1');

      expect(apiClient.get).toHaveBeenCalledWith('/documents/1');
      expect(result).toEqual(mockDocument);
    });
  });

  describe('upload', () => {
    it('should upload a file with progress callback', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse = { id: '1', file_name: 'test.pdf' };
      const progressCallback = vi.fn();

      vi.mocked(apiClient.uploadFile).mockResolvedValue(mockResponse);

      const result = await documentsApi.upload(mockFile, progressCallback);

      expect(apiClient.uploadFile).toHaveBeenCalledWith(
        '/documents/upload',
        mockFile,
        progressCallback
      );
      expect(result).toEqual(mockResponse);
    });

    it('should upload a file without progress callback', async () => {
      const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const mockResponse = { id: '1', file_name: 'test.pdf' };

      vi.mocked(apiClient.uploadFile).mockResolvedValue(mockResponse);

      const result = await documentsApi.upload(mockFile);

      expect(apiClient.uploadFile).toHaveBeenCalledWith(
        '/documents/upload',
        mockFile,
        undefined
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('delete', () => {
    it('should delete a document by id', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue(undefined);

      await documentsApi.delete('1');

      expect(apiClient.delete).toHaveBeenCalledWith('/documents/1');
    });
  });

  describe('process', () => {
    it('should trigger document processing', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ status: 'processing' });

      const result = await documentsApi.process('1');

      expect(apiClient.post).toHaveBeenCalledWith('/documents/1/process');
      expect(result).toEqual({ status: 'processing' });
    });
  });

  describe('getContent', () => {
    it('should fetch document content without page parameter', async () => {
      const mockContent = { text: 'Document content', metadata: {} };
      vi.mocked(apiClient.get).mockResolvedValue(mockContent);

      const result = await documentsApi.getContent('1');

      expect(apiClient.get).toHaveBeenCalledWith('/documents/1/content');
      expect(result).toEqual(mockContent);
    });

    it('should fetch document content with page parameter', async () => {
      const mockContent = { text: 'Page 2 content', metadata: {} };
      vi.mocked(apiClient.get).mockResolvedValue(mockContent);

      const result = await documentsApi.getContent('1', 2);

      expect(apiClient.get).toHaveBeenCalledWith('/documents/1/content?page=2');
      expect(result).toEqual(mockContent);
    });
  });

  describe('getStrategies', () => {
    it('should fetch document strategies', async () => {
      const mockStrategies = [
        { id: '1', name: 'Strategy 1' },
        { id: '2', name: 'Strategy 2' },
      ];
      vi.mocked(apiClient.get).mockResolvedValue(mockStrategies);

      const result = await documentsApi.getStrategies('1');

      expect(apiClient.get).toHaveBeenCalledWith('/documents/1/strategies');
      expect(result).toEqual(mockStrategies);
    });
  });

  describe('download', () => {
    it('should download a document', async () => {
      const mockBlob = new Blob(['file content']);
      vi.mocked(apiClient.get).mockResolvedValue(mockBlob);

      await documentsApi.download('1', 'test.pdf');

      expect(apiClient.get).toHaveBeenCalledWith('/documents/1/download', {
        responseType: 'blob',
      });

      // Verify download link creation
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'test.pdf');
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockLink.remove).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });
});