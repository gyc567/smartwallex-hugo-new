#!/usr/bin/env python3
"""
中文交易信号发送测试
测试完整的中文信号发送流程
"""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_sender import TelegramSender
from signal_translator import SignalTranslator

def test_chinese_signal_sending():
    """测试中文信号发送"""
    print("🧪 中文交易信号发送测试")
    print("=" * 50)
    
    # 设置环境变量
    os.environ['TELEGRAM_BOT_TOKEN'] = '8209835379:AAEarEFcbfR8fDJMFw16A0h1MqWHliFTnYE'
    os.environ['TELEGRAM_CHANNEL_ID'] = '-1003168613592'
    
    # 创建发送器
    sender = TelegramSender(
        os.environ['TELEGRAM_BOT_TOKEN'],
        os.environ['TELEGRAM_CHANNEL_ID']
    )
    
    # 测试信号数据（你提供的示例）
    test_signal = {
        "symbol": "SOL/USDT",
        "signal": "BUY",
        "entry_price": "$159.0",
        "stop_loss": "$156.1",
        "take_profit": "$164.1",
        "confidence": "70%",
        "risk_reward_ratio": "1:1.8",
        "timeframe": "1h",
        "market_condition": "Support test",
        "timestamp": "2025-09-30 10:34:30 UTC",
        "indicators": {
            "rsi": "36",
            "macd": "Bullish crossover",
            "volume": "Normal",
            "moving_averages": "Golden cross"
        }
    }
    
    print("📋 测试信号:")
    print(json.dumps(test_signal, indent=2, ensure_ascii=False))
    
    print("\n🔍 验证中文翻译器:")
    translator = SignalTranslator()
    chinese_message = translator.format_professional_chinese(test_signal)
    print(chinese_message)
    
    print("\n📤 发送到Telegram频道:")
    success = sender.send_trading_signal(test_signal)
    
    if success:
        print("✅ 中文信号发送成功！")
        print("📱 请检查你的私人频道是否收到了中文信号")
        return True
    else:
        print("❌ 中文信号发送失败")
        return False

def test_market_summary():
    """测试市场摘要发送"""
    print("\n" + "=" * 50)
    print("📊 市场摘要发送测试")
    
    sender = TelegramSender(
        os.environ['TELEGRAM_BOT_TOKEN'],
        os.environ['TELEGRAM_CHANNEL_ID']
    )
    
    # 市场摘要数据
    market_summary = {
        "date": "2025-09-30",
        "time": "10:34:30 UTC",
        "market_sentiment": "Bearish",
        "volatility": "High",
        "dominant_trend": "Down",
        "key_levels": {
            "btc_support": "$40,802",
            "btc_resistance": "$47,902",
            "eth_support": "$2,590",
            "eth_resistance": "$3,146"
        }
    }
    
    translator = SignalTranslator()
    summary_message = translator.translate_market_summary(market_summary)
    
    print("📋 市场摘要:")
    print(summary_message)
    
    success = sender.send_message(summary_message)
    
    if success:
        print("✅ 市场摘要发送成功！")
        return True
    else:
        print("❌ 市场摘要发送失败")
        return False

def main():
    """主函数"""
    print("🚀 中文交易信号测试系统")
    print("=" * 60)
    
    # 测试中文信号发送
    signal_success = test_chinese_signal_sending()
    
    # 测试市场摘要
    summary_success = test_market_summary()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    if signal_success:
        print("✅ 中文信号发送: 通过")
    else:
        print("❌ 中文信号发送: 失败")
        
    if summary_success:
        print("✅ 市场摘要发送: 通过")
    else:
        print("❌ 市场摘要发送: 失败")
    
    if signal_success and summary_success:
        print("\n🎉 所有中文信号测试通过！")
        print("📱 请检查你的私人频道: 比特财商|加密信号")
        print("频道ID: -1003168613592")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")
    
    return signal_success and summary_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)