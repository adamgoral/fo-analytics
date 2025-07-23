"""Tests for data loader."""

import pytest
from datetime import date, timedelta
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock

from services.backtesting.data_loader import DataLoader
from models.strategy import AssetClass


@pytest.mark.asyncio
class TestDataLoader:
    """Test the data loader service."""
    
    @pytest.fixture
    def data_loader(self):
        """Create a data loader instance."""
        return DataLoader()
    
    @pytest.fixture
    def mock_data(self):
        """Create mock market data."""
        dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
        data = pd.DataFrame({
            "Open": [100 + i for i in range(30)],
            "High": [102 + i for i in range(30)],
            "Low": [99 + i for i in range(30)],
            "Close": [101 + i for i in range(30)],
            "Volume": [1000000] * 30
        }, index=dates)
        return data
    
    async def test_get_default_symbols(self, data_loader):
        """Test getting default symbols for asset classes."""
        # Test equity defaults
        symbols = data_loader._get_default_symbols(AssetClass.EQUITY)
        assert "SPY" in symbols
        assert isinstance(symbols, list)
        
        # Test fixed income defaults
        symbols = data_loader._get_default_symbols(AssetClass.FIXED_INCOME)
        assert "AGG" in symbols or "BND" in symbols
        
        # Test commodity defaults
        symbols = data_loader._get_default_symbols(AssetClass.COMMODITY)
        assert any(s in symbols for s in ["DJP", "GSG", "DBC"])
        
        # Test crypto defaults
        symbols = data_loader._get_default_symbols(AssetClass.CRYPTO)
        assert "BTC-USD" in symbols
    
    @patch("yfinance.Ticker")
    async def test_load_data_single_symbol(self, mock_ticker, data_loader, mock_data):
        """Test loading data for a single symbol."""
        # Mock yfinance response
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Load data
        result = await data_loader.load_data(
            asset_class=AssetClass.EQUITY,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            symbols=["SPY"]
        )
        
        # Verify
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 30
        assert all(col in result.columns for col in ["Open", "High", "Low", "Close", "Volume"])
        
        # Verify yfinance was called correctly
        mock_ticker.assert_called_once_with("SPY")
        mock_ticker_instance.history.assert_called_once_with(
            start="2023-01-01",
            end="2023-01-31",
            interval="1d",
            auto_adjust=True,
            prepost=False
        )
    
    @patch("yfinance.Ticker")
    async def test_load_data_multiple_symbols(self, mock_ticker, data_loader, mock_data):
        """Test loading data for multiple symbols."""
        # Mock yfinance response
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Load data for multiple symbols
        result = await data_loader.load_data(
            asset_class=AssetClass.EQUITY,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            symbols=["SPY", "QQQ", "IWM"]
        )
        
        # Should use first symbol as primary
        assert isinstance(result, pd.DataFrame)
        assert "Open" in result.columns
        
        # Should have additional symbol data
        assert mock_ticker.call_count >= 1  # At least called for primary symbol
    
    @patch("yfinance.Ticker")
    async def test_load_data_with_missing_data(self, mock_ticker, data_loader):
        """Test handling missing data."""
        # Mock empty response
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        # Should raise ValueError for empty data
        with pytest.raises(ValueError, match="No data available"):
            await data_loader.load_data(
                asset_class=AssetClass.EQUITY,
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 31),
                symbols=["INVALID"]
            )
    
    async def test_prepare_data_for_backtesting(self, data_loader, mock_data):
        """Test data preparation for backtesting."""
        # Add some NaN values
        mock_data.loc[mock_data.index[5], "Close"] = None
        
        # Prepare data
        result = data_loader._prepare_data_for_backtesting(mock_data, "SPY")
        
        # Verify NaN handling
        assert not result["Close"].isna().any()
        
        # Verify volume is integer
        assert result["Volume"].dtype == int
        
        # Verify index is sorted
        assert result.index.is_monotonic_increasing
    
    @patch("yfinance.Ticker")
    async def test_get_latest_price(self, mock_ticker, data_loader):
        """Test getting latest price."""
        # Mock ticker info
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            "regularMarketPrice": 450.50,
            "previousClose": 449.00
        }
        mock_ticker.return_value = mock_ticker_instance
        
        # Get latest price
        price = await data_loader.get_latest_price("SPY")
        
        assert price == 450.50
        mock_ticker.assert_called_once_with("SPY")
    
    @patch("yfinance.Ticker")
    async def test_get_latest_price_fallback(self, mock_ticker, data_loader):
        """Test getting latest price with fallback."""
        # Mock ticker info without regularMarketPrice
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {"previousClose": 449.00}
        mock_ticker.return_value = mock_ticker_instance
        
        # Should fall back to previous close
        price = await data_loader.get_latest_price("SPY")
        assert price == 449.00
    
    @patch("yfinance.Ticker")
    async def test_get_symbol_info(self, mock_ticker, data_loader):
        """Test getting symbol information."""
        # Mock ticker info
        mock_info = {
            "symbol": "SPY",
            "longName": "SPDR S&P 500 ETF Trust",
            "regularMarketPrice": 450.50,
            "marketCap": 415000000000,
            "trailingPE": 24.5
        }
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = mock_info
        mock_ticker.return_value = mock_ticker_instance
        
        # Get symbol info
        info = await data_loader.get_symbol_info("SPY")
        
        assert info == mock_info
        assert info["symbol"] == "SPY"
        assert info["regularMarketPrice"] == 450.50