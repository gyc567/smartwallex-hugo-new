#!/usr/bin/env python3
"""
Bitget集成测试脚本
测试Bitget API集成和实时数据获取功能
"""

import sys
import logging
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from bitget_client import BitgetClient, create_bitget_client
from price_fetcher import PriceFetcher
from trading_signal_generator import TradingSignalGenerator

def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_bitget_client():
    """测试Bitget客户端"""
    print("🔍 测试Bitget客户端...")
    print("-" * 50)
    
    try:
        client = create_bitget_client()
        
        # 测试获取单个币种价格
        test_symbols = ['BTC', 'ETH', 'BNB']
        
        for symbol in test_symbols:
            print(f"\n📊 获取 {symbol} 价格数据...")
            ticker = client.get_ticker(symbol)
            
            if ticker:
                print(f"💰 {symbol}: ${ticker.price:,.2f}")
                print(f"   24h变化: {ticker.price_change_percent_24h:+.2f}%")
                print(f"   24h区间: ${ticker.low_24h:,.2f} - ${ticker.high_24h:,.2f}")
                print(f"   成交量: {ticker.volume_24h:,.2f}")
                print(f"   更新时间: {ticker.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   数据来源: {ticker.data_source}")
            else:
                print(f"❌ 获取 {symbol} 价格失败")
        
        # 测试获取所有币种价格
        print(f"\n📊 批量获取所有币种价格...")
        all_prices = client.get_all_tickers()
        
        print(f"✅ 成功获取 {len(all_prices)} 个币种的价格数据")
        
        return True
        
    except Exception as e:
        print(f"❌ Bitget客户端测试失败: {e}")
        return False

def test_price_fetcher_with_bitget():
    """测试价格获取器（集成Bitget）"""
    print("\n🔍 测试价格获取器（集成Bitget）...")
    print("-" * 50)
    
    try:
        fetcher = PriceFetcher()
        
        # 测试获取BTC价格
        print(f"\n📊 获取BTC实时价格...")
        btc_price = fetcher.get_realtime_price('BTC')
        
        if btc_price:
            print(f"💰 BTC: ${btc_price.price:,.2f}")
            print(f"   24h变化: {btc_price.price_change_percent_24h:+.2f}%")
            print(f"   24h区间: ${btc_price.low_24h:,.2f} - ${btc_price.high_24h:,.2f}")
            print(f"   成交量: ${btc_price.volume_24h:,.0f}")
            print(f"   数据来源: {btc_price.data_source}")
            print(f"   更新时间: {btc_price.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print("❌ 获取BTC价格失败")
        
        # 测试获取所有币种价格
        print(f"\n📊 获取所有币种价格...")
        all_prices = fetcher.get_all_prices()
        
        print(f"✅ 成功获取 {len(all_prices)} 个币种的价格数据")
        
        for symbol, price_data in all_prices.items():
            if price_data:
                print(f"💰 {symbol}: ${price_data.price:,.2f} (来源: {price_data.data_source})")
        
        return True
        
    except Exception as e:
        print(f"❌ 价格获取器测试失败: {e}")
        return False

def test_trading_signal_generator():
    """测试交易信号生成器（使用实时数据）"""
    print("\n🔍 测试交易信号生成器（使用实时数据）...")
    print("-" * 50)
    
    try:
        generator = TradingSignalGenerator()
        
        # 生成交易信号
        print(f"\n📊 生成交易信号...")
        signals = generator.generate_signals(3)
        
        print(f"✅ 成功生成 {len(signals)} 个交易信号")
        
        for i, signal in enumerate(signals, 1):
            print(f"\n🎯 信号 #{i}")
            print(f"   交易对: {signal['symbol']}")
            print(f"   信号: {signal['signal']}")
            print(f"   当前价格: {signal['current_price']}")
            print(f"   入场价格: {signal['entry_price']}")
            print(f"   止损: {signal['stop_loss']}")
            print(f"   止盈: {signal['take_profit']}")
            print(f"   信心度: {signal['confidence']}")
            print(f"   风险回报比: {signal['risk_reward_ratio']}")
            print(f"   价格来源: {signal['price_source']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 交易信号生成器测试失败: {e}")
        return False

def test_api_keys():
    """测试API密钥配置"""
    print("\n🔍 测试API密钥配置...")
    print("-" * 50)
    
    # 检查环境变量
    import os
    
    api_key = os.getenv('BITGET_API_KEY')
    secret_key = os.getenv('BITGET_SECRET_KEY')
    passphrase = os.getenv('BITGET_PASSPHRASE')
    
    print(f"BITGET_API_KEY: {'已配置' if api_key else '未配置'}")
    print(f"BITGET_SECRET_KEY: {'已配置' if secret_key else '未配置'}")
    print(f"BITGET_PASSPHRASE: {'已配置' if passphrase else '未配置'}")
    
    if not api_key or not secret_key:
        print("\n⚠️  注意: Bitget API密钥未完全配置，将使用公开API（可能有限制）")
        print("   请设置环境变量或修改 .env.local 文件")
        return False
    
    return True

def main():
    """主函数"""
    setup_logging()
    
    print("🚀 Bitget集成测试开始")
    print("=" * 60)
    
    # 测试API密钥配置
    api_keys_ok = test_api_keys()
    
    # 测试Bitget客户端
    bitget_ok = test_bitget_client()
    
    # 测试价格获取器
    fetcher_ok = test_price_fetcher_with_bitget()
    
    # 测试交易信号生成器
    generator_ok = test_trading_signal_generator()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   API密钥配置: {'✅' if api_keys_ok else '⚠️'}")
    print(f"   Bitget客户端: {'✅' if bitget_ok else '❌'}")
    print(f"   价格获取器: {'✅' if fetcher_ok else '❌'}")
    print(f"   交易信号生成器: {'✅' if generator_ok else '❌'}")
    
    all_passed = all([bitget_ok, fetcher_ok, generator_ok])
    
    if all_passed:
        print("\n🎉 所有测试通过！Bitget集成成功")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查配置和网络连接")
        return 1

if __name__ == "__main__":
    exit(main())