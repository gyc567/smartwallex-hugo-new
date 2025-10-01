#!/usr/bin/env python3
"""
Bitget API客户端
提供Bitget交易所的实时价格数据和交易信息获取功能
"""

import os
import json
import time
import hmac
import hashlib
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
import requests
import sys
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


@dataclass
class BitgetPriceData:
    """Bitget价格数据结构"""
    symbol: str
    price: float
    price_change_24h: float
    price_change_percent_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    quote_volume_24h: float
    last_update: datetime
    data_source: str = "Bitget"


class BitgetClient:
    """Bitget API客户端"""
    
    # API配置
    BASE_URL = "https://api.bitget.com"
    API_VERSION = "/api/v1/spot"
    
    def __init__(self, api_key: str = None, secret_key: str = None, passphrase: str = None):
        """初始化Bitget客户端
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            passphrase: 密码短语
        """
        self.logger = logging.getLogger(__name__)
        
        # 从环境变量或参数获取API密钥
        self.api_key = api_key or os.getenv('BITGET_API_KEY')
        self.secret_key = secret_key or os.getenv('BITGET_SECRET_KEY')
        self.passphrase = passphrase or os.getenv('BITGET_PASSPHRASE')
        
        self.session = requests.Session()
        self.session.timeout = 10
        
        # 币种映射 (内部符号 -> Bitget符号)
        self.symbol_mapping = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT', 
            'BNB': 'BNBUSDT',
            'SOL': 'SOLUSDT',
            'BCH': 'BCHUSDT'
        }
        
        self.logger.info("Bitget客户端初始化完成")
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """生成API签名
        
        Args:
            timestamp: 时间戳
            method: HTTP方法
            request_path: 请求路径
            body: 请求体
            
        Returns:
            签名字符串
        """
        if not self.secret_key:
            return ""
            
        message = timestamp + method.upper() + request_path + body
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, body: Dict = None, signed: bool = False) -> Optional[Dict]:
        """发送API请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            body: 请求体
            signed: 是否需要签名
            
        Returns:
            API响应数据
        """
        try:
            url = self.BASE_URL + endpoint
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SmartWallex-TradingBot/1.0'
            }
            
            # 如果需要签名，添加认证头
            if signed and self.api_key and self.secret_key:
                timestamp = str(int(time.time() * 1000))
                request_path = endpoint
                body_str = json.dumps(body) if body else ""
                signature = self._generate_signature(timestamp, method, request_path, body_str)
                
                headers.update({
                    'ACCESS-KEY': self.api_key,
                    'ACCESS-SIGN': signature,
                    'ACCESS-TIMESTAMP': timestamp,
                    'ACCESS-PASSPHRASE': self.passphrase or ''
                })
            
            # 发送请求
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=body)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API响应码
            if data.get('code') == '00000':
                return data.get('data')
            else:
                self.logger.error(f"Bitget API错误: {data.get('msg', '未知错误')} (code: {data.get('code')})")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Bitget API请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Bitget API请求异常: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[BitgetPriceData]:
        """获取单个币种的24小时 ticker 数据
        
        Args:
            symbol: 币种符号 (如 'BTC')
            
        Returns:
            BitgetPriceData对象，失败时返回None
        """
        try:
            # 转换符号格式 (Bitget需要 _SPBL 后缀)
            bitget_symbol = f"{self.symbol_mapping.get(symbol.upper())}_SPBL"
            if not bitget_symbol or bitget_symbol == "_SPBL":
                self.logger.error(f"不支持的币种: {symbol}")
                return None
            
            # 使用公开API端点
            endpoint = f"/api/spot/v1/market/ticker"
            params = {'symbol': bitget_symbol}
            
            data = self._make_request('GET', endpoint, params=params)
            
            if data:
                # Bitget返回的数据结构
                ticker_data = data
                
                current_price = float(ticker_data.get('close', '0'))
                high_24h = float(ticker_data.get('high24h', '0'))
                low_24h = float(ticker_data.get('low24h', '0'))
                volume_24h = float(ticker_data.get('baseVol', '0'))
                quote_volume_24h = float(ticker_data.get('quoteVol', '0'))
                
                # 计算价格变化
                open_24h = float(ticker_data.get('openUtc0', current_price))
                price_change_24h = current_price - open_24h
                price_change_percent_24h = (price_change_24h / open_24h * 100) if open_24h > 0 else 0
                
                return BitgetPriceData(
                    symbol=symbol,
                    price=current_price,
                    price_change_24h=price_change_24h,
                    price_change_percent_24h=price_change_percent_24h,
                    high_24h=high_24h,
                    low_24h=low_24h,
                    volume_24h=volume_24h,
                    quote_volume_24h=quote_volume_24h,
                    last_update=datetime.now(timezone.utc)
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} ticker 数据失败: {e}")
            return None
    
    def get_all_tickers(self) -> Dict[str, BitgetPriceData]:
        """获取所有支持的币种价格数据
        
        Returns:
            所有币种的价格数据字典
        """
        results = {}
        
        for symbol in self.symbol_mapping.keys():
            ticker_data = self.get_ticker(symbol)
            if ticker_data:
                results[symbol] = ticker_data
            else:
                self.logger.warning(f"无法获取 {symbol} 的价格数据")
        
        return results
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """获取订单簿数据
        
        Args:
            symbol: 币种符号
            limit: 深度限制
            
        Returns:
            订单簿数据
        """
        try:
            bitget_symbol = self.symbol_mapping.get(symbol.upper())
            if not bitget_symbol:
                return None
            
            endpoint = f"{self.API_VERSION}/market/orderbook"
            params = {
                'symbol': bitget_symbol,
                'limit': limit
            }
            
            return self._make_request('GET', endpoint, params=params)
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} 订单簿失败: {e}")
            return None
    
    def get_candles(self, symbol: str, interval: str = '1H', limit: int = 100) -> Optional[List[Dict]]:
        """获取K线数据
        
        Args:
            symbol: 币种符号
            interval: 时间间隔 ('1m', '5m', '15m', '30m', '1H', '4H', '6H', '1D')
            limit: 返回条数限制
            
        Returns:
            K线数据列表
        """
        try:
            bitget_symbol = self.symbol_mapping.get(symbol.upper())
            if not bitget_symbol:
                return None
            
            endpoint = f"{self.API_VERSION}/market/candles"
            params = {
                'symbol': bitget_symbol,
                'granularity': interval,
                'limit': limit
            }
            
            return self._make_request('GET', endpoint, params=params)
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} K线数据失败: {e}")
            return None


def create_bitget_client() -> BitgetClient:
    """创建Bitget客户端实例
    
    Returns:
        BitgetClient实例
    """
    return BitgetClient()


def main():
    """主函数 - 测试Bitget API功能"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 开始测试Bitget API功能...")
    print("=" * 60)
    
    # 创建客户端
    client = create_bitget_client()
    
    # 测试获取单个币种价格
    test_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'BCH']
    
    for symbol in test_symbols:
        print(f"\n📊 获取 {symbol} 价格数据...")
        ticker = client.get_ticker(symbol)
        
        if ticker:
            print(f"💰 {symbol}: ${ticker.price:,.2f}")
            print(f"   24h变化: {ticker.price_change_percent_24h:+.2f}%")
            print(f"   24h区间: ${ticker.low_24h:,.2f} - ${ticker.high_24h:,.2f}")
            print(f"   成交量: {ticker.volume_24h:,.2f}")
            print(f"   更新时间: {ticker.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print(f"❌ 获取 {symbol} 价格失败")
    
    # 测试获取所有币种价格
    print(f"\n📊 获取所有币种价格...")
    all_prices = client.get_all_tickers()
    
    print(f"✅ 成功获取 {len(all_prices)} 个币种的价格数据")
    
    print("\n" + "=" * 60)
    print("✅ Bitget API测试完成")


if __name__ == "__main__":
    main()