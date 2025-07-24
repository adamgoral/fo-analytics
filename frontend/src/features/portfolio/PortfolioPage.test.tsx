import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import PortfolioPage from './PortfolioPage';
import portfolioReducer from '../../store/portfolioSlice';
import authReducer from '../../store/slices/authSlice';
import chatReducer from '../../store/slices/chatSlice';

const createTestStore = () =>
  configureStore({
    reducer: {
      auth: authReducer,
      chat: chatReducer,
      portfolio: portfolioReducer,
    },
  });

describe('PortfolioPage', () => {
  it('renders the portfolio analytics dashboard', () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <MemoryRouter>
          <PortfolioPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Portfolio Analytics Dashboard')).toBeInTheDocument();
  });

  it('displays the key metrics cards', () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <MemoryRouter>
          <PortfolioPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Total Portfolio Value')).toBeInTheDocument();
    expect(screen.getByText('Total P&L')).toBeInTheDocument();
    expect(screen.getByText('Asset Classes')).toBeInTheDocument();
    expect(screen.getByText('Positions')).toBeInTheDocument();
  });

  it('renders all tabs', () => {
    const store = createTestStore();

    render(
      <Provider store={store}>
        <MemoryRouter>
          <PortfolioPage />
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Optimization')).toBeInTheDocument();
    expect(screen.getByText('Efficient Frontier')).toBeInTheDocument();
    expect(screen.getByText('Risk Analysis')).toBeInTheDocument();
    expect(screen.getByText('Multi-Strategy')).toBeInTheDocument();
  });
});