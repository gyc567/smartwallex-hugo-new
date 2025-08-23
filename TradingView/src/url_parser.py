"""
TradingView URL解析器
解析TradingView图表链接，提取交易对、时间周期等参数
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional


class TradingViewURLParser:
    """TradingView URL解析器"""
    
    def __init__(self):
        self.base_patterns = {
            'symbol': r'symbol=([^&]+)',
            'interval': r'interval=([^&]+)',
            'exchange': r'exchange=([^&]+)'
        }
    
    def parse_url(self, url: str) -> Dict[str, str]:
        """
        解析TradingView URL
        
        Args:
            url: TradingView图表链接
            
        Returns:
            包含交易对、周期等信息的字典
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            result = {
                'url': url,
                'symbol': self._extract_symbol(query_params, url),
                'interval': self._extract_interval(query_params, url),
                'exchange': self._extract_exchange(query_params, url),
                'valid': True
            }
            
            # 验证必要参数
            if not result['symbol']:
                result['valid'] = False
                result['error'] = 'Symbol not found'
            
            return result
            
        except Exception as e:
            return {
                'url': url,
                'valid': False,
                'error': str(e)
            }
    
    def _extract_symbol(self, query_params: Dict, url: str) -> Optional[str]:
        """提取交易对符号"""
        # 从查询参数中提取
        if 'symbol' in query_params:
            return query_params['symbol'][0]
        
        # 从URL路径中提取
        symbol_match = re.search(self.base_patterns['symbol'], url)
        if symbol_match:
            return symbol_match.group(1)
        
        # 默认BTC/USDT
        return 'BTCUSDT'
    
    def _extract_interval(self, query_params: Dict, url: str) -> str:
        """提取时间周期"""
        # 从查询参数中提取
        if 'interval' in query_params:
            return query_params['interval'][0]
        
        # 从URL中提取
        interval_match = re.search(self.base_patterns['interval'], url)
        if interval_match:
            return interval_match.group(1)
        
        # 默认4小时
        return '4h'
    
    def _extract_exchange(self, query_params: Dict, url: str) -> str:
        """提取交易所"""
        # 从查询参数中提取
        if 'exchange' in query_params:
            return query_params['exchange'][0]
        
        # 从URL中提取
        exchange_match = re.search(self.base_patterns['exchange'], url)
        if exchange_match:
            return exchange_match.group(1)
        
        # 默认币安
        return 'BINANCE'
    
    def normalize_symbol(self, symbol: str) -> str:
        """标准化交易对符号"""
        # 移除交易所前缀
        symbol = symbol.upper()
        if ':' in symbol:
            symbol = symbol.split(':')[1]
        
        # 确保格式正确
        if 'USDT' not in symbol and 'BTC' in symbol:
            return f"{symbol}USDT"
        
        return symbol
    
    def normalize_interval(self, interval: str) -> str:
        """标准化时间周期"""
        interval_map = {
            '1': '1m',
            '3': '3m',
            '5': '5m',
            '15': '15m',
            '30': '30m',
            '60': '1h',
            '120': '2h',
            '240': '4h',
            '360': '6h',
            '480': '8h',
            '720': '12h',
            'D': '1d',
            '1D': '1d',
            'W': '1w',
            '1W': '1w'
        }
        
        return interval_map.get(interval, interval)