#!/usr/bin/env python3
"""
加密货币价格数据获取器

提供轻量级、高内聚的实时价格数据获取功能
支持多个数据源，确保高可用性和数据准确性
"""

import os
import json
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
import requests
import sys

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from crypto_swap_config import SUPPORTED_CRYPTOS
from bitget_client import BitgetClient, BitgetPriceData
from notification_service import notify_realtime_data_failure, notify_trading_pause


@dataclass
class PriceData:
    """价格数据结构"""
    symbol: str
    price: float
    price_change_24h: float
    price_change_percent_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    last_update: datetime
    data_source: str


class PriceFetcher:
    """价格获取器核心类"""
    
    def __init__(self):
        """初始化价格获取器"""
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        
        # 备用数据源列表（按优先级排序）
        self.data_sources = [
            self._fetch_from_bitget,  # Bitget作为首选数据源
            self._fetch_from_binance,
            self._fetch_from_coinpaprika,
            self._fetch_from_coingecko,
            self._fetch_from_coinmarketcap
        ]
        
        # 初始化Bitget客户端
        self.bitget_client = BitgetClient()
    
    def get_realtime_price(self, symbol: str) -> Optional[PriceData]:
        """获取实时价格数据 - 严格要求Bitget数据源
        
        Args:
            symbol: 加密货币符号 (如 'BTC')
            
        Returns:
            PriceData对象，失败时抛出异常
            
        Raises:
            RuntimeError: 当Bitget数据源失败时抛出
        """
        try:
            # 检查缓存
            cached_data = self._get_from_cache(symbol)
            if cached_data:
                self.logger.info(f"从缓存获取 {symbol} 价格数据")
                return cached_data
            
            # 严格要求使用Bitget数据源，失败时报错
            self.logger.info(f"正在从Bitget获取 {symbol} 实时价格数据...")
            price_data = self._fetch_from_bitget(symbol)
            
            if price_data:
                # 更新缓存
                self._update_cache(symbol, price_data)
                self.logger.info(f"成功获取 {symbol} Bitget实时价格数据: ${price_data.price:,.2f}")
                return price_data
            else:
                # Bitget数据源失败，立即报错并通知用户
                error_msg = f"❌ CRITICAL: Bitget实时数据源失败，无法获取 {symbol} 价格数据。交易程序已暂停。"
                self.logger.error(error_msg)
                
                # 通知用户
                notify_realtime_data_failure(symbol, error_msg, {
                    "data_source": "Bitget",
                    "function": "get_realtime_price",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                raise RuntimeError(error_msg)
                
        except Exception as e:
            error_msg = f"❌ CRITICAL: 获取 {symbol} 实时价格数据失败: {e}。交易程序已暂停。"
            self.logger.error(error_msg)
            
            # 通知用户
            notify_realtime_data_failure(symbol, str(e), {
                "data_source": "Bitget",
                "function": "get_realtime_price",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "original_error": str(e)
            })
            
            raise RuntimeError(error_msg)
    
    def get_all_prices(self) -> Dict[str, PriceData]:
        """获取所有支持的加密货币价格 - 严格要求Bitget数据源
        
        Returns:
            所有币种的价格数据字典
            
        Raises:
            RuntimeError: 当任何币种的Bitget数据源失败时抛出
        """
        prices = {}
        failed_symbols = []
        
        for symbol in SUPPORTED_CRYPTOS.keys():
            try:
                price_data = self.get_realtime_price(symbol)
                if price_data:
                    prices[symbol] = price_data
                else:
                    # 这种情况不应该发生，因为get_realtime_price会抛出异常
                    failed_symbols.append(symbol)
            except RuntimeError as e:
                # Bitget数据源失败，记录失败的币种
                failed_symbols.append(symbol)
                self.logger.error(f"获取 {symbol} 价格失败: {e}")
                continue
        
        # 如果有任何币种失败，报错并暂停交易
        if failed_symbols:
            error_msg = f"❌ CRITICAL: 以下币种Bitget实时数据获取失败: {', '.join(failed_symbols)}。为确保交易安全，程序已暂停。"
            self.logger.error(error_msg)
            
            # 通知用户交易暂停
            notify_trading_pause(error_msg, {
                "failed_symbols": failed_symbols,
                "total_symbols": len(SUPPORTED_CRYPTOS.keys()),
                "success_symbols": list(prices.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            raise RuntimeError(error_msg)
        
        if not prices:
            error_msg = "❌ CRITICAL: 无法获取任何币种的实时价格数据。交易程序已暂停。"
            self.logger.error(error_msg)
            
            # 通知用户交易暂停
            notify_trading_pause(error_msg, {
                "failed_symbols": list(SUPPORTED_CRYPTOS.keys()),
                "total_symbols": len(SUPPORTED_CRYPTOS.keys()),
                "success_symbols": [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            raise RuntimeError(error_msg)
        
        return prices
    
    def _get_from_cache(self, symbol: str) -> Optional[PriceData]:
        """从缓存获取价格数据"""
        if symbol in self.cache:
            cached_data, cached_time = self.cache[symbol]
            if time.time() - cached_time < self.cache_timeout:
                return cached_data
        return None
    
    def _update_cache(self, symbol: str, price_data: PriceData):
        """更新价格缓存"""
        self.cache[symbol] = (price_data, time.time())
    
    def _fetch_from_coinmarketcap(self, symbol: str) -> Optional[PriceData]:
        """从CoinMarketCap获取价格数据"""
        try:
            # CoinMarketCap API (需要API key，这里使用公开接口)
            url = f"https://api.coinmarketcap.com/data-api/v3/cryptocurrency/detail/chart?id={self._get_coin_id(symbol)}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') == 0:
                points = data.get('data', {}).get('points', [])
                if points:
                    latest_point = points[-1]
                    current_price = latest_point['v'][0]
                    
                    # 计算24小时变化
                    if len(points) >= 2:
                        prev_price = points[0]['v'][0]
                        price_change = current_price - prev_price
                        price_change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0
                    else:
                        price_change = 0
                        price_change_percent = 0
                    
                    return PriceData(
                        symbol=symbol,
                        price=current_price,
                        price_change_24h=price_change,
                        price_change_percent_24h=price_change_percent,
                        high_24h=current_price * 1.02,  # 近似值
                        low_24h=current_price * 0.98,   # 近似值
                        volume_24h=0,  # CoinMarketCap免费接口不提供volume
                        last_update=datetime.now(timezone.utc),
                        data_source="CoinMarketCap"
                    )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"CoinMarketCap获取 {symbol} 价格失败: {e}")
            return None
    
    def _fetch_from_bitget(self, symbol: str) -> Optional[PriceData]:
        """从Bitget获取价格数据"""
        try:
            # 使用Bitget客户端获取数据
            bitget_data = self.bitget_client.get_ticker(symbol)
            
            if bitget_data:
                # 转换数据格式
                return PriceData(
                    symbol=bitget_data.symbol,
                    price=bitget_data.price,
                    price_change_24h=bitget_data.price_change_24h,
                    price_change_percent_24h=bitget_data.price_change_percent_24h,
                    high_24h=bitget_data.high_24h,
                    low_24h=bitget_data.low_24h,
                    volume_24h=bitget_data.volume_24h,
                    last_update=bitget_data.last_update,
                    data_source="Bitget"
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Bitget获取 {symbol} 价格失败: {e}")
            return None
    
    def _fetch_from_binance(self, symbol: str) -> Optional[PriceData]:
        """从Binance获取价格数据"""
        try:
            # Binance公开API
            ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            klines_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1d&limit=1"
            
            # 获取24小时统计数据
            ticker_response = requests.get(ticker_url, timeout=10)
            ticker_response.raise_for_status()
            ticker_data = ticker_response.json()
            
            # 获取K线数据以获得更精确的信息
            klines_response = requests.get(klines_url, timeout=10)
            klines_response.raise_for_status()
            klines_data = klines_response.json()
            
            if ticker_data and klines_data:
                current_price = float(ticker_data['lastPrice'])
                prev_close_price = float(klines_data[0][1])  # 昨收价
                
                price_change = float(ticker_data['priceChange'])
                price_change_percent = float(ticker_data['priceChangePercent'])
                high_24h = float(ticker_data['highPrice'])
                low_24h = float(ticker_data['lowPrice'])
                volume_24h = float(ticker_data['volume'])
                
                return PriceData(
                    symbol=symbol,
                    price=current_price,
                    price_change_24h=price_change,
                    price_change_percent_24h=price_change_percent,
                    high_24h=high_24h,
                    low_24h=low_24h,
                    volume_24h=volume_24h,
                    last_update=datetime.now(timezone.utc),
                    data_source="Binance"
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Binance获取 {symbol} 价格失败: {e}")
            return None
    
    def _fetch_from_coinpaprika(self, symbol: str) -> Optional[PriceData]:
        """从CoinPaprika获取价格数据"""
        try:
            # CoinPaprika API (免费，无需API key)
            coin_id = self._get_coinpaprika_id(symbol)
            if not coin_id:
                return None
                
            url = f"https://api.coinpaprika.com/v1/tickers/{coin_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data:
                current_price = float(data['quotes']['USD']['price'])
                price_change_24h = float(data['quotes']['USD']['price_change_24h'])
                price_change_percent_24h = float(data['quotes']['USD']['percent_change_24h'])
                high_24h = float(data['quotes']['USD']['high_24h'])
                low_24h = float(data['quotes']['USD']['low_24h'])
                volume_24h = float(data['quotes']['USD']['volume_24h'])
                
                return PriceData(
                    symbol=symbol,
                    price=current_price,
                    price_change_24h=price_change_24h,
                    price_change_percent_24h=price_change_percent_24h,
                    high_24h=high_24h,
                    low_24h=low_24h,
                    volume_24h=volume_24h,
                    last_update=datetime.now(timezone.utc),
                    data_source="CoinPaprika"
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"CoinPaprika获取 {symbol} 价格失败: {e}")
            return None
    
    def _fetch_from_coingecko(self, symbol: str) -> Optional[PriceData]:
        """从CoinGecko获取价格数据"""
        try:
            # CoinGecko API (免费，有rate limit)
            coin_id = self._get_coingecko_id(symbol)
            if not coin_id:
                return None
                
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_24hr_high_low=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if coin_id in data:
                coin_data = data[coin_id]
                current_price = float(coin_data['usd'])
                price_change_24h = float(coin_data['usd_24h_change']) if 'usd_24h_change' in coin_data else 0
                high_24h = float(coin_data['usd_24h_high']) if 'usd_24h_high' in coin_data else current_price
                low_24h = float(coin_data['usd_24h_low']) if 'usd_24h_low' in coin_data else current_price
                volume_24h = float(coin_data['usd_24h_vol']) if 'usd_24h_vol' in coin_data else 0
                
                price_change_percent_24h = (price_change_24h / (current_price - price_change_24h)) * 100 if (current_price - price_change_24h) > 0 else 0
                
                return PriceData(
                    symbol=symbol,
                    price=current_price,
                    price_change_24h=price_change_24h,
                    price_change_percent_24h=price_change_percent_24h,
                    high_24h=high_24h,
                    low_24h=low_24h,
                    volume_24h=volume_24h,
                    last_update=datetime.now(timezone.utc),
                    data_source="CoinGecko"
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"CoinGecko获取 {symbol} 价格失败: {e}")
            return None
    
    def _get_coin_id(self, symbol: str) -> str:
        """获取CoinMarketCap的coin ID"""
        coin_ids = {
            'BTC': '1',
            'ETH': '1027',
            'BNB': '1839',
            'SOL': '5426',
            'BCH': '1961'
        }
        return coin_ids.get(symbol, '')
    
    def _get_coinpaprika_id(self, symbol: str) -> str:
        """获取CoinPaprika的coin ID"""
        coin_ids = {
            'BTC': 'btc-bitcoin',
            'ETH': 'eth-ethereum',
            'BNB': 'bnb-binance-coin',
            'SOL': 'sol-solana',
            'BCH': 'bch-bitcoin-cash'
        }
        return coin_ids.get(symbol, '')
    
    def _get_coingecko_id(self, symbol: str) -> str:
        """获取CoinGecko的coin ID"""
        coin_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'BCH': 'bitcoin-cash'
        }
        return coin_ids.get(symbol, '')


def main():
    """主函数 - 测试价格获取功能"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = PriceFetcher()
    print("🔍 开始测试加密货币价格获取功能...")
    print("=" * 60)
    
    # 测试获取所有币种价格
    prices = fetcher.get_all_prices()
    
    for symbol, price_data in prices.items():
        if price_data:
            print(f"💰 {symbol}: ${price_data.price:,.2f}")
            print(f"   24h变化: {price_data.price_change_percent_24h:+.2f}%")
            print(f"   24h区间: ${price_data.low_24h:,.2f} - ${price_data.high_24h:,.2f}")
            print(f"   来源: {price_data.data_source}")
            print(f"   更新时间: {price_data.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print()
        else:
            print(f"❌ {symbol}: 获取价格失败")
    
    print("=" * 60)
    print("✅ 价格获取测试完成")


if __name__ == "__main__":
    main()