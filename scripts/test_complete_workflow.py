#!/usr/bin/env python3
"""
完整工作流程测试
验证AI交易信号生成器与GitHub Actions配置的集成
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def test_workflow_integration():
    """测试GitHub Actions工作流集成"""
    print("🔍 测试GitHub Actions工作流集成...")
    
    # 1. 验证工作流文件包含AI配置
    workflow_file = Path("../.github/workflows/daily-crypto-signals.yml")
    if not workflow_file.exists():
        print("   ❌ 工作流文件不存在")
        return False
    
    with open(workflow_file, 'r') as f:
        workflow_content = f.read()
    
    # 检查AI配置
    ai_checks = [
        ("OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}", "OPENAI_API_KEY环境变量"),
        ("OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}", "OPENAI_BASE_URL环境变量"),
        ("trading_signal_generator_wrapper.py", "AI包装器脚本"),
        ("--use-ai", "AI模式参数"),
        ("AI Expert Analysis", "AI分析类型"),
        ("Bitget + AI Model", "AI数据源")
    ]
    
    all_passed = True
    for check_text, description in ai_checks:
        if check_text in workflow_content:
            print(f"   ✅ 工作流包含{description}")
        else:
            print(f"   ❌ 工作流缺少{description}")
            all_passed = False
    
    return all_passed

def test_cli_integration():
    """测试CLI集成"""
    print("\n🔍 测试CLI集成...")
    
    try:
        # 测试传统模式
        result = subprocess.run([
            sys.executable, "trading_signal_generator_wrapper.py",
            "--use-traditional", "--count", "1", "--format", "json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            if "signals" in output and len(output["signals"]) > 0:
                print("   ✅ 传统模式CLI正常工作")
            else:
                print("   ❌ 传统模式CLI输出格式错误")
                return False
        else:
            print(f"   ❌ 传统模式CLI失败: {result.stderr}")
            return False
        
        # 测试AI模式（回退到传统模式）
        result = subprocess.run([
            sys.executable, "trading_signal_generator_wrapper.py",
            "--use-ai", "--count", "1", "--format", "json"
        ], capture_output=True, text=True, timeout=30, env={**dict(os.environ), "OPENAI_API_KEY": "test-key"})
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            if "signals" in output and len(output["signals"]) > 0:
                print("   ✅ AI模式CLI回退机制正常")
            else:
                print("   ❌ AI模式CLI输出格式错误")
                return False
        else:
            print(f"   ❌ AI模式CLI失败: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ CLI集成测试失败: {e}")
        return False

def test_signal_format():
    """测试信号格式"""
    print("\n🔍 测试信号格式...")
    
    try:
        # 生成一个信号进行格式验证
        result = subprocess.run([
            sys.executable, "trading_signal_generator_wrapper.py",
            "--use-traditional", "--count", "1", "--format", "json"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"   ❌ 信号生成失败: {result.stderr}")
            return False
        
        output = json.loads(result.stdout)
        signals = output.get("signals", [])
        
        if len(signals) == 0:
            print("   ❌ 没有生成信号")
            return False
        
        signal = signals[0]
        
        # 验证必需字段
        required_fields = [
            "symbol", "signal", "current_price", "entry_price",
            "stop_loss", "take_profit", "confidence", "timestamp",
            "timeframe", "market_condition", "risk_reward_ratio",
            "indicators", "price_source", "analysis_type", "data_source"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in signal:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"   ❌ 信号缺少字段: {missing_fields}")
            return False
        
        # 验证字段格式
        checks = [
            (signal["signal"] in ["BUY", "SELL", "HOLD"], "信号方向有效"),
            (signal["price_source"] == "realtime", "价格来源正确"),
            ("%" in signal["confidence"], "置信度格式正确"),
            (":" in signal["risk_reward_ratio"], "风险回报比格式正确"),
            (signal["analysis_type"] in ["Technical Analysis", "AI Expert Analysis"], "分析类型有效"),
            (signal["data_source"].startswith("Bitget"), "数据源格式正确")
        ]
        
        all_passed = True
        for condition, description in checks:
            if condition:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ 信号格式测试失败: {e}")
        return False

def test_telegram_format():
    """测试Telegram消息格式"""
    print("\n🔍 测试Telegram消息格式...")
    
    try:
        # 测试消息格式化
        from telegram_sender import TelegramSender
        
        test_signal = {
            "symbol": "BTC/USDT",
            "signal": "BUY",
            "current_price": "$50,000.00",
            "entry_price": "$49,500.00",
            "stop_loss": "$48,500.00",
            "take_profit": "$54,500.00",
            "confidence": "85%",
            "timestamp": "2025-10-01 12:00:00 UTC",
            "indicators": {
                "rsi": "42",
                "macd": "Golden Cross",
                "volume": "Above Average",
                "moving_averages": "Price above MA50"
            },
            "risk_reward_ratio": "1:2.5",
            "timeframe": "4h",
            "market_condition": "AI Analyzed",
            "price_source": "ai_realtime",
            "mcp_analysis": "上涨积累：RSI 42，MACD金叉",
            "risk_warning": "BTC联动回调风险",
            "ai_analysis": "基于实时市场数据的AI分析"
        }
        
        sender = TelegramSender("test_token", "@test_channel")
        formatted_message = sender._format_trading_signal(test_signal)
        
        # 验证消息格式
        required_elements = [
            "买入信号", "BTC/USDT", "$49,500.00", "$48,500.00",
            "$54,500.00", "85%", "1:2.5", "4h", "RSI指标", "MACD信号",
            "风险提示", "高风险"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in formatted_message:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"   ❌ 消息缺少元素: {missing_elements}")
            return False
        
        print("   ✅ Telegram消息格式正确")
        print(f"   📧 消息长度: {len(formatted_message)} 字符")
        return True
        
    except Exception as e:
        print(f"   ❌ Telegram格式测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理机制"""
    print("\n🔍 测试错误处理机制...")
    
    try:
        # 测试无效币种处理
        result = subprocess.run([
            sys.executable, "-c", """
import sys
sys.path.append('scripts')
from trading_signal_generator_wrapper import TradingSignalGeneratorWrapper
wrapper = TradingSignalGeneratorWrapper(use_ai=False)
try:
    wrapper.generate_signals(-1)
    print("❌ 应该抛出异常")
    sys.exit(1)
except Exception as e:
    print(f"✅ 正确处理无效参数: {type(e).__name__}")
    sys.exit(0)
"""
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ 错误处理机制正常")
            return True
        else:
            print(f"   ❌ 错误处理测试失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ 错误处理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 完整工作流程测试")
    print("="*60)
    
    # 运行各项测试
    tests = [
        ("GitHub Actions工作流集成", test_workflow_integration),
        ("CLI集成", test_cli_integration),
        ("信号格式", test_signal_format),
        ("Telegram消息格式", test_telegram_format),
        ("错误处理机制", test_error_handling)
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
    print("📊 完整工作流程测试结果汇总:")
    
    passed = 0
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有完整工作流程测试通过！")
        print("\n✅ 系统完全就绪:")
        print("   • GitHub Actions工作流已配置AI支持")
        print("   • CLI接口完全兼容")
        print("   • 信号格式符合标准")
        print("   • Telegram消息格式正确")
        print("   • 错误处理机制完善")
        print("\n🚀 AI驱动的交易信号系统已准备好部署！")
        print("\n📋 部署前准备:")
        print("   1. 在GitHub Secrets中设置 OPENAI_API_KEY")
        print("   2. 在GitHub Secrets中设置 OPENAI_BASE_URL") 
        print("   3. 确保Telegram bot token和channel ID已配置")
        print("   4. 测试环境变量配置")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败")
        return 1

if __name__ == '__main__':
    import os
    exit(main())