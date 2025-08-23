"""
数据获取模块
从多个API源获取K线数据和市场数据
"""

import ccxt
import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.exchanges = self._init_exchanges()
        self.logger = logging.getLogger(__name__)
    
    def _init_exchanges(self) -> Dict:
        """初始化交易所连接"""
        exchanges = {}
        
        try:
            # 币安
            exchanges['binance'] = ccxt.binance({
                'apiKey': self.config.get('binance_api_key'),
                'secret': self.config.get('binance_secret'),
                'sandbox': False,
                'rateLimit': 1200,
            })
            
            # OKX
            exchanges['okx'] = ccxt.okx({
                'apiKey': self.config.get('okx_api_key'),
                'secret': self.config.get('okx_secret'),
                'password': self.config.get('okx_passphrase'),
                'sandbox': False,
            })
            
        except Exception as e:
            self.logger.warning(f"交易所初始化警告: {e}")
        
        return exchanges
    
    def get_kline_data(self, symbol: str, interval: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对符号 (如 BTC/USDT)
            interval: 时间周期 (如 4h)
            limit: K线数量
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        # 标准化交易对格式
        normalized_symbol = self._normalize_symbol_for_ccxt(symbol)
        
        # 尝试多个数据源
        for exchange_name in ['binance', 'okx']:
            try:
                data = self._fetch_from_exchange(exchange_name, normalized_symbol, interval, limit)
                if data is not None:
                    self.logger.info(f"从 {exchange_name} 获取数据成功")
                    return data
            except Exception as e:
                self.logger.warning(f"从 {exchange_name} 获取数据失败: {e}")
        
        # 尝试免费API
        try:
            data = self._fetch_from_free_api(symbol, interval, limit)
            if data is not None:
                self.logger.info("从免费API获取数据成功")
                return data
        except Exception as e:
            self.logger.error(f"所有数据源获取失败: {e}")
        
        return None
    
    def _fetch_from_exchange(self, exchange_name: str, symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
        """从交易所获取数据"""
        if exchange_name not in self.exchanges:
            return None
        
        exchange = self.exchanges[exchange_name]
        
        # 获取OHLCV数据
        ohlcv = exchange.fetch_ohlcv(symbol, interval, limit=limit)
        
        if not ohlcv:
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _fetch_from_free_api(self, symbol: str, interval: str, limit: int) -> Optional[pd.DataFrame]:
        """从免费API获取数据"""
        # 使用CoinGecko API获取价格数据
        try:
            # 简化的符号映射
            coin_id = self._get_coingecko_id(symbol)
            
            # 获取历史价格
            days = self._interval_to_days(interval, limit)
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if '1h' in interval or '4h' in interval else 'daily'
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'prices' in data:
                # 转换为DataFrame
                prices = data['prices']
                df = pd.DataFrame(prices, columns=['timestamp', 'price'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                # 简化的OHLCV数据（使用价格作为OHLC）
                df['open'] = df['price']
                df['high'] = df['price']
                df['low'] = df['price']
                df['close'] = df['price']
                df['volume'] = 0  # CoinGecko免费版没有成交量
                
                return df[['open', 'high', 'low', 'close', 'volume']].tail(limit)
        
        except Exception as e:
            self.logger.error(f"免费API获取失败: {e}")
        
        return None
    
    def _normalize_symbol_for_ccxt(self, symbol: str) -> str:
        """为CCXT标准化交易对符号"""
        symbol = symbol.upper().replace('USDT', '/USDT').replace('BTC', 'BTC')
        if '/' not in symbol:
            symbol = f"{symbol}/USDT"
        return symbol
    
    def _get_coingecko_id(self, symbol: str) -> str:
        """获取CoinGecko币种ID"""
        id_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'AVAX': 'avalanche-2'
        }
        
        base_symbol = symbol.replace('USDT', '').replace('/USDT', '')
        return id_map.get(base_symbol, 'bitcoin')
    
    def _interval_to_days(self, interval: str, limit: int) -> int:
        """将时间间隔转换为天数"""
        interval_hours = {
            '1h': 1,
            '4h': 4,
            '1d': 24,
            '1w': 168
        }
        
        hours = interval_hours.get(interval, 4)
        return max(1, (limit * hours) // 24)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取当前价格"""
        normalized_symbol = self._normalize_symbol_for_ccxt(symbol)
        
        for exchange_name in ['binance', 'okx']:
            try:
                if exchange_name in self.exchanges:
                    ticker = self.exchanges[exchange_name].fetch_ticker(normalized_symbol)
                    return ticker['last']
            except Exception as e:
                self.logger.warning(f"从 {exchange_name} 获取价格失败: {e}")
        
        return None