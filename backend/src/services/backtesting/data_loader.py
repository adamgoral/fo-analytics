"""Data loader for fetching historical market data."""

import asyncio
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import pandas as pd
import yfinance as yf
import structlog
from concurrent.futures import ThreadPoolExecutor

from models.strategy import AssetClass

logger = structlog.get_logger(__name__)


class DataLoader:
    """Load historical market data for backtesting."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._symbol_mapping = {
            AssetClass.EQUITY: {
                "default": ["SPY", "QQQ", "IWM"],
                "sectors": {
                    "technology": ["XLK", "VGT", "FTEC"],
                    "financials": ["XLF", "VFH", "FNCL"],
                    "healthcare": ["XLV", "VHT", "FHLC"],
                    "energy": ["XLE", "VDE", "FENY"],
                    "consumer": ["XLY", "VCR", "FDIS"]
                }
            },
            AssetClass.FIXED_INCOME: {
                "default": ["AGG", "BND", "TLT"],
                "treasury": ["SHY", "IEF", "TLT", "TLH"],
                "corporate": ["LQD", "VCSH", "VCIT", "VCLT"],
                "high_yield": ["HYG", "JNK", "SJNK", "HYLS"]
            },
            AssetClass.COMMODITY: {
                "default": ["DJP", "GSG", "DBC"],
                "precious_metals": ["GLD", "SLV", "PPLT"],
                "energy": ["USO", "UNG", "BNO"],
                "agriculture": ["DBA", "CORN", "WEAT", "SOYB"]
            },
            AssetClass.CURRENCY: {
                "default": ["DXY", "UUP", "FXE"],
                "major_pairs": ["FXE", "FXY", "FXB", "FXC", "FXA"]
            },
            AssetClass.CRYPTO: {
                "default": ["BTC-USD", "ETH-USD"],
                "major": ["BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD"]
            },
            AssetClass.MULTI_ASSET: {
                "default": ["SPY", "AGG", "GLD", "DXY"]
            }
        }
    
    async def load_data(
        self,
        asset_class: AssetClass,
        start_date: date,
        end_date: date,
        symbols: Optional[List[str]] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Load historical data for the given parameters."""
        # Use provided symbols or defaults for asset class
        if not symbols:
            symbols = self._get_default_symbols(asset_class)
        
        logger.info(
            "Loading market data",
            asset_class=asset_class,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        # Load data asynchronously
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            self.executor,
            self._fetch_data_sync,
            symbols,
            start_date,
            end_date,
            interval
        )
        
        # Ensure we have required columns for backtesting.py
        if data.empty:
            raise ValueError("No data available for the specified parameters")
        
        return self._prepare_data_for_backtesting(data, symbols[0])
    
    def _get_default_symbols(self, asset_class: AssetClass) -> List[str]:
        """Get default symbols for an asset class."""
        mapping = self._symbol_mapping.get(asset_class, {})
        return mapping.get("default", ["SPY"])
    
    def _fetch_data_sync(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str
    ) -> pd.DataFrame:
        """Fetch data synchronously using yfinance."""
        try:
            # For single symbol
            if len(symbols) == 1:
                ticker = yf.Ticker(symbols[0])
                data = ticker.history(
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    interval=interval,
                    auto_adjust=True,
                    prepost=False
                )
                return data
            
            # For multiple symbols (portfolio backtesting)
            # For now, we'll use the first symbol as primary
            # In future, we can implement portfolio strategies
            ticker = yf.Ticker(symbols[0])
            data = ticker.history(
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                interval=interval,
                auto_adjust=True,
                prepost=False
            )
            
            # Store additional symbols data for portfolio strategies
            for symbol in symbols[1:]:
                ticker = yf.Ticker(symbol)
                symbol_data = ticker.history(
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    interval=interval,
                    auto_adjust=True,
                    prepost=False
                )
                if not symbol_data.empty:
                    # Add symbol data with prefixed column names
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        if col in symbol_data.columns:
                            data[f"{symbol}_{col}"] = symbol_data[col]
            
            return data
            
        except Exception as e:
            logger.error(
                "Failed to fetch market data",
                symbols=symbols,
                error=str(e)
            )
            raise ValueError(f"Failed to fetch data: {str(e)}")
    
    def _prepare_data_for_backtesting(
        self,
        data: pd.DataFrame,
        primary_symbol: str
    ) -> pd.DataFrame:
        """Prepare data in the format expected by backtesting.py."""
        # Ensure we have the required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # Sort by date
        data = data.sort_index()
        
        # Handle any missing values
        data = data.fillna(method='ffill').fillna(method='bfill')
        
        # Ensure volume is integer
        if 'Volume' in data.columns:
            data['Volume'] = data['Volume'].astype(int)
        
        logger.info(
            "Prepared data for backtesting",
            symbol=primary_symbol,
            start_date=data.index[0],
            end_date=data.index[-1],
            rows=len(data)
        )
        
        return data
    
    async def load_returns_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Load returns data for multiple symbols.
        
        Args:
            symbols: List of symbols to load
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval
            
        Returns:
            DataFrame with returns for each symbol as columns
        """
        returns_dict = {}
        
        # Load data for each symbol
        for symbol in symbols:
            try:
                # Convert datetime to date if needed
                start_dt = start_date.date() if isinstance(start_date, datetime) else start_date
                end_dt = end_date.date() if isinstance(end_date, datetime) else end_date
                
                data = await self.load_data(
                    asset_class=AssetClass.EQUITY,  # Default to equity
                    start_date=start_dt,
                    end_date=end_dt,
                    symbols=[symbol],
                    interval=interval
                )
                if not data.empty:
                    # Calculate returns from close prices
                    returns = data['Close'].pct_change().dropna()
                    returns_dict[symbol] = returns
            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {str(e)}")
                continue
        
        # Create DataFrame from returns
        if returns_dict:
            returns_df = pd.DataFrame(returns_dict)
            # Drop any rows with NaN values
            returns_df = returns_df.dropna()
            
            logger.info(
                "Returns data loaded",
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                shape=returns_df.shape
            )
            
            return returns_df
        else:
            logger.warning("No returns data loaded for any symbols")
            return pd.DataFrame()
    
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol."""
        try:
            loop = asyncio.get_event_loop()
            price = await loop.run_in_executor(
                self.executor,
                self._get_latest_price_sync,
                symbol
            )
            return price
        except Exception as e:
            logger.error("Failed to get latest price", symbol=symbol, error=str(e))
            return None
    
    def _get_latest_price_sync(self, symbol: str) -> float:
        """Get latest price synchronously."""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get('regularMarketPrice', info.get('previousClose', 0))
    
    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a symbol."""
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                self.executor,
                self._get_symbol_info_sync,
                symbol
            )
            return info
        except Exception as e:
            logger.error("Failed to get symbol info", symbol=symbol, error=str(e))
            return {}
    
    def _get_symbol_info_sync(self, symbol: str) -> Dict[str, Any]:
        """Get symbol info synchronously."""
        ticker = yf.Ticker(symbol)
        return ticker.info
    
    def __del__(self):
        """Clean up thread pool on deletion."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)