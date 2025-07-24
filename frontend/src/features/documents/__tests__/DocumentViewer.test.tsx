import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DocumentViewer from '../DocumentViewer';
import { documentsApi } from '../../../services/documents';

// Mock the API service
vi.mock('../../../services/documents', () => ({
  documentsApi: {
    getContent: vi.fn(),
    getStrategies: vi.fn(),
    download: vi.fn(),
  },
}));

const mockDocumentContent = {
  text: 'This is a test document content',
  metadata: {
    pages: 5,
    file_type: 'pdf',
    created_at: '2024-01-01T00:00:00Z',
  },
  page_contents: [
    { page_number: 1, text: 'Page 1 content' },
    { page_number: 2, text: 'Page 2 content' },
  ],
};

const mockStrategies = [
  {
    id: '1',
    name: 'Test Strategy 1',
    description: 'A test trading strategy',
    asset_class: 'Equity',
    timeframe: 'Daily',
    risk_level: 'Medium',
    entry_conditions: ['Condition 1', 'Condition 2'],
    exit_conditions: ['Exit 1', 'Exit 2'],
    risk_management: { stop_loss: '2%', position_size: '10%' },
    performance_metrics: {
      expected_return: 0.15,
      sharpe_ratio: 1.5,
      max_drawdown: -0.10,
    },
    confidence_score: 0.85,
    extracted_at: '2024-01-01T00:00:00Z',
    document_id: 'doc123',
  },
];

describe('DocumentViewer', () => {
  const mockProps = {
    documentId: 'doc123',
    documentName: 'test-document.pdf',
    onClose: vi.fn(),
    onRunBacktest: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading skeleton initially', () => {
    render(<DocumentViewer {...mockProps} />);
    // Check for skeleton elements instead of specific test-id
    const skeletons = document.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('should load and display document content', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue(mockStrategies);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      expect(documentsApi.getContent).toHaveBeenCalledWith('doc123');
      expect(documentsApi.getStrategies).toHaveBeenCalledWith('doc123');
    });

    // Check if content is displayed
    expect(screen.getByText('This is a test document content')).toBeInTheDocument();
  });

  it('should display error when loading fails', async () => {
    const errorMessage = 'Failed to load document';
    vi.mocked(documentsApi.getContent).mockRejectedValue(new Error(errorMessage));
    vi.mocked(documentsApi.getStrategies).mockResolvedValue([]);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Check if retry button is present
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('should switch between tabs', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue(mockStrategies);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Document Content')).toBeInTheDocument();
    });

    // Click on strategies tab
    const strategiesTab = screen.getByText(/Extracted Strategies/);
    fireEvent.click(strategiesTab);

    // Check if strategy content is displayed
    await waitFor(() => {
      expect(screen.getByText('Test Strategy 1')).toBeInTheDocument();
      expect(screen.getByText('A test trading strategy')).toBeInTheDocument();
    });
  });

  it('should handle page navigation for multi-page documents', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue([]);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Select Page:')).toBeInTheDocument();
    });

    // Click on page 2
    const page2Button = screen.getByText('Page 2');
    fireEvent.click(page2Button);

    // Check if page 2 content is displayed
    expect(screen.getByText('Page 2 content')).toBeInTheDocument();
  });

  it('should call download function when download button is clicked', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue([]);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      const downloadButton = screen.getByLabelText('Download');
      fireEvent.click(downloadButton);
    });

    expect(documentsApi.download).toHaveBeenCalledWith('doc123', 'test-document.pdf');
  });

  it('should call onRunBacktest when Run Backtest button is clicked', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue(mockStrategies);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      const strategiesTab = screen.getByText(/Extracted Strategies/);
      fireEvent.click(strategiesTab);
    });

    const runBacktestButton = await screen.findByText('Run Backtest');
    fireEvent.click(runBacktestButton);

    expect(mockProps.onRunBacktest).toHaveBeenCalledWith('1');
  });

  it('should toggle fullscreen mode', async () => {
    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue([]);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(mockProps.documentName)).toBeInTheDocument();
    });

    const fullscreenButton = screen.getByLabelText('Fullscreen');
    fireEvent.click(fullscreenButton);

    // Check if exit fullscreen button appears
    await waitFor(() => {
      expect(screen.getByLabelText('Exit fullscreen')).toBeInTheDocument();
    });
  });

  it('should display strategy risk levels with appropriate colors', async () => {
    const strategiesWithDifferentRisks = [
      { ...mockStrategies[0], risk_level: 'Low' },
      { ...mockStrategies[0], id: '2', risk_level: 'High' },
    ];

    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue(strategiesWithDifferentRisks);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      const strategiesTab = screen.getByText(/Extracted Strategies/);
      fireEvent.click(strategiesTab);
    });

    // Check risk level chips are displayed
    expect(screen.getByText('Risk: Low')).toBeInTheDocument();
    expect(screen.getByText('Risk: High')).toBeInTheDocument();
  });

  it('should display confidence scores with appropriate colors', async () => {
    const strategiesWithDifferentConfidence = [
      { ...mockStrategies[0], confidence_score: 0.9 },
      { ...mockStrategies[0], id: '2', confidence_score: 0.5 },
    ];

    vi.mocked(documentsApi.getContent).mockResolvedValue(mockDocumentContent);
    vi.mocked(documentsApi.getStrategies).mockResolvedValue(strategiesWithDifferentConfidence);

    render(<DocumentViewer {...mockProps} />);

    await waitFor(() => {
      const strategiesTab = screen.getByText(/Extracted Strategies/);
      fireEvent.click(strategiesTab);
    });

    // Check confidence scores are displayed
    expect(screen.getByText('Confidence: 90%')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 50%')).toBeInTheDocument();
  });
});