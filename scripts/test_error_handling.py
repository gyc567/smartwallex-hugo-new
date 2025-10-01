#!/usr/bin/env python3
"""
错误处理机制测试脚本
测试新的实时数据失败处理逻辑
"""

import sys
import logging
from pathlib import Path

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from price_fetcher import PriceFetcher
from trading_signal_generator import TradingSignalGenerator
from crypto_swap_analyzer import CryptoSwapAnalyzer
from notification_service import NotificationService

def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_price_fetcher_error_handling():
    """测试价格获取器的错误处理"""
    print("🔍 测试价格获取器错误处理...")
    print("-" * 50)
    
    try:
        fetcher = PriceFetcher()
        
        # 测试正常获取价格
        print("✅ 测试正常价格获取:")
        btc_price = fetcher.get_realtime_price('BTC')
        print(f"   BTC价格: ${btc_price.price:,.2f} (来源: {btc_price.data_source})")
        
        # 测试批量获取价格
        print("\n✅ 测试批量价格获取:")
        all_prices = fetcher.get_all_prices()
        print(f"   成功获取 {len(all_prices)} 个币种的价格数据")
        for symbol, price_data in all_prices.items():
            print(f"   {symbol}: ${price_data.price:,.2f}")
        
        return True
        
    except RuntimeError as e:
        print(f"❌ 价格获取器RuntimeError: {e}")
        return False
    except Exception as e:
        print(f"❌ 价格获取器测试失败: {e}")
        return False

def test_trading_signal_generator_error_handling():
    """测试交易信号生成器的错误处理"""
    print("\n🔍 测试交易信号生成器错误处理...")
    print("-" * 50)
    
    try:
        generator = TradingSignalGenerator()
        
        # 测试正常生成信号
        print("✅ 测试正常信号生成:")
        signals = generator.generate_signals(3)
        print(f"   成功生成 {len(signals)} 个交易信号")
        
        for i, signal in enumerate(signals, 1):
            print(f"\n🎯 信号 #{i}")
            print(f"   交易对: {signal['symbol']}")
            print(f"   信号: {signal['signal']}")
            print(f"   当前价格: {signal['current_price']}")
            print(f"   价格来源: {signal['price_source']}")
        
        return True
        
    except RuntimeError as e:
        print(f"❌ 交易信号生成器RuntimeError: {e}")
        return False
    except Exception as e:
        print(f"❌ 交易信号生成器测试失败: {e}")
        return False

def test_crypto_swap_analyzer_error_handling():
    """测试加密货币合约分析器的错误处理"""
    print("\n🔍 测试加密货币合约分析器错误处理...")
    print("-" * 50)
    
    try:
        analyzer = CryptoSwapAnalyzer()
        
        # 测试正常分析流程
        print("✅ 测试正常分析流程:")
        success = analyzer.run_analysis()
        
        if success:
            print("   ✅ 分析流程成功完成")
            return True
        else:
            print("   ❌ 分析流程失败")
            return False
        
    except RuntimeError as e:
        print(f"❌ 合约分析器RuntimeError: {e}")
        return False
    except Exception as e:
        print(f"❌ 合约分析器测试失败: {e}")
        return False

def test_notification_service():
    """测试通知服务"""
    print("\n🔍 测试通知服务...")
    print("-" * 50)
    
    try:
        notification_service = NotificationService()
        
        # 测试实时数据失败通知
        print("✅ 测试实时数据失败通知:")
        notification_service.notify_realtime_data_failure(
            "BTC", 
            "测试错误 - 网络连接超时",
            {"test": True, "timestamp": "2025-09-30T12:00:00Z"}
        )
        
        # 测试交易暂停通知
        print("\n✅ 测试交易暂停通知:")
        notification_service.notify_trading_pause(
            "测试暂停 - 数据源异常",
            {"test": True, "failed_symbols": ["BTC", "ETH"]}
        )
        
        return True
        
    except Exception as e:
        print(f"❌ 通知服务测试失败: {e}")
        return False

def test_error_scenarios():
    """测试特定的错误场景"""
    print("\n🔍 测试错误场景处理...")
    print("-" * 50)
    
    try:
        # 测试不存在的币种
        fetcher = PriceFetcher()
        
        print("✅ 测试不支持的币种:")
        try:
            fetcher.get_realtime_price('INVALID')
            print("   ⚠️  应该抛出异常但没有抛出")
            return False
        except RuntimeError as e:
            print(f"   ✅ 正确抛出异常: {str(e)[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误场景测试失败: {e}")
        return False

def main():
    """主函数"""
    setup_logging()
    
    print("🚀 错误处理机制测试开始")
    print("="*60)
    
    # 运行各项测试
    tests = [
        ("价格获取器", test_price_fetcher_error_handling),
        ("交易信号生成器", test_trading_signal_generator_error_handling),
        ("加密货币合约分析器", test_crypto_swap_analyzer_error_handling),
        ("通知服务", test_notification_service),
        ("错误场景", test_error_scenarios)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ {test_name} 测试执行失败: {e}")
            results[test_name] = False
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有错误处理机制测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败，请检查相关功能")
        return 1

if __name__ == "__main__":
    exit(main())