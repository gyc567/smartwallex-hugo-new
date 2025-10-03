#!/usr/bin/env python3
"""
中文信号格式化器测试套件
确保100%测试覆盖率
"""

import unittest
import sys
import os

# 添加scripts目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from chinese_signal_formatter import ChineseSignalFormatter


class TestChineseSignalFormatter(unittest.TestCase):
    """中文信号格式化器测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.formatter = ChineseSignalFormatter()
        
        # 完整的测试信号数据
        self.complete_signal = {
            "symbol": "BCH/USDT",
            "signal": "BUY",
            "entry_price": "$596",
            "stop_loss": "$579", 
            "take_profit": "$626",
            "confidence": "66%",
            "risk_reward_ratio": "1:1.7",
            "timeframe": "4h",
            "market_condition": "Resistance test",
            "indicators": {
                "rsi": "40",
                "macd": "Positive divergence"
            }
        }
        
        self.partial_signal = {
            "symbol": "ETH/USDT",
            "signal": "SELL",
            "entry_price": "$2500",
            "stop_loss": "$2550",
            "take_profit": "$2400",
            "confidence": "75%"
            # 缺少其他字段
        }
        
        self.empty_signal = {}
    
    def test_complete_signal_formatting(self):
        """测试完整信号格式化"""
        result = self.formatter.format_signal(self.complete_signal)
        
        # 验证关键字段被正确翻译和格式化（注意HTML格式）
        self.assertIn("BCH/USDT永续合约信号", result)
        self.assertIn("做多", result)
        self.assertIn("入场价</b>：$596", result)
        self.assertIn("止损价</b>：$579", result)
        self.assertIn("止盈价</b>：$626", result)
        self.assertIn("风险回报比</b>：1:1.7", result)
        self.assertIn("信心度</b>：66%", result)
        self.assertIn("RSI指标</b>：40", result)
        self.assertIn("正背离", result)  # MACD翻译
        self.assertIn("阻力位测试", result)  # 市场状况翻译
        self.assertIn("时间框架</b>：4h", result)
        self.assertIn("风险提示", result)
    
    def test_partial_signal_formatting(self):
        """测试部分信号格式化"""
        result = self.formatter.format_signal(self.partial_signal)
        
        # 验证基本字段存在（注意HTML格式）
        self.assertIn("ETH/USDT永续合约信号", result)
        self.assertIn("做空", result)
        self.assertIn("入场价</b>：$2500", result)
        self.assertIn("止损价</b>：$2550", result)
        self.assertIn("止盈价</b>：$2400", result)
        self.assertIn("信心度</b>：75%", result)
        
        # 验证缺失字段使用默认值
        self.assertIn("风险回报比</b>：N/A", result)
        self.assertIn("RSI指标</b>：N/A", result)
        self.assertIn("MACD信号</b>：N/A", result)
        self.assertIn("时间框架</b>：N/A", result)
        self.assertIn("市场状况</b>：N/A", result)
    
    def test_empty_signal_formatting(self):
        """测试空信号格式化"""
        result = self.formatter.format_signal(self.empty_signal)
        
        # 验证空信号的处理（注意HTML格式）
        self.assertIn("Unknown永续合约信号", result)
        self.assertIn("Unknown", result)
        self.assertIn("入场价</b>：N/A", result)
        self.assertIn("止损价</b>：N/A", result)
        self.assertIn("止盈价</b>：N/A", result)
        self.assertIn("风险提示", result)
    
    def test_signal_translations(self):
        """测试信号翻译"""
        # 测试BUY翻译
        buy_signal = {"signal": "BUY"}
        result = self.formatter.format_signal(buy_signal)
        self.assertIn("做多", result)
        
        # 测试SELL翻译
        sell_signal = {"signal": "SELL"}
        result = self.formatter.format_signal(sell_signal)
        self.assertIn("做空", result)
        
        # 测试HOLD翻译
        hold_signal = {"signal": "HOLD"}
        result = self.formatter.format_signal(hold_signal)
        self.assertIn("持仓观望", result)
        
        # 测试未知信号
        unknown_signal = {"signal": "UNKNOWN"}
        result = self.formatter.format_signal(unknown_signal)
        self.assertIn("UNKNOWN", result)
    
    def test_condition_translations(self):
        """测试市场状况翻译"""
        test_cases = [
            ("Support test", "支撑位测试"),
            ("Resistance test", "阻力位测试"),
            ("Breakout", "突破"),
            ("Pullback", "回调"),
            ("Consolidation", "盘整"),
            ("Trend continuation", "趋势延续"),
            ("Trend reversal", "趋势反转"),
            ("AI Analyzed", "AI分析"),
            ("Unknown Condition", "Unknown Condition")  # 未知状况
        ]
        
        for english, expected_chinese in test_cases:
            signal = {"market_condition": english}
            result = self.formatter.format_signal(signal)
            self.assertIn(expected_chinese, result)
    
    def test_macd_translations(self):
        """测试MACD信号翻译"""
        test_cases = [
            ("Bullish crossover", "金叉"),
            ("Bearish crossover", "死叉"),
            ("Positive divergence", "正背离"),
            ("Negative divergence", "负背离"),
            ("Near zero line", "接近零轴"),
            ("Strong bullish", "强势看涨"),
            ("Strong bearish", "强势看跌"),
            ("Unknown MACD", "Unknown MACD")  # 未知MACD
        ]
        
        for english, expected_chinese in test_cases:
            signal = {"indicators": {"macd": english}}
            result = self.formatter.format_signal(signal)
            self.assertIn(expected_chinese, result)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效数据类型
        invalid_signal = "not a dict"
        result = self.formatter.format_signal(invalid_signal)  # type: ignore
        
        # 应该返回英文后备格式
        self.assertIn("SmartWallex Trading Signal", result)
        self.assertIn("Symbol:", result)
        self.assertIn("Risk Warning", result)
    
    def test_fallback_english_format(self):
        """测试英文后备格式"""
        # 创建一个会触发错误的信号
        class ProblematicSignal:
            def get(self, key, default=None):
                raise Exception("Test error")
        
        # 模拟格式化器内部错误
        original_format = self.formatter.format_signal
        def mock_format(signal_data):
            raise Exception("Test formatting error")
        
        self.formatter.format_signal = mock_format
        
        try:
            # 应该触发后备英文格式
            result = self.formatter._fallback_english_format(self.complete_signal)
            
            # 验证英文格式
            self.assertIn("SmartWallex Trading Signal", result)
            self.assertIn("Symbol:", result)
            self.assertIn("Signal:", result)
            self.assertIn("Entry:", result)
            self.assertIn("Stop Loss:", result)
            self.assertIn("Take Profit:", result)
            self.assertIn("Risk Warning", result)
        finally:
            # 恢复原始方法
            self.formatter.format_signal = original_format
    
    def test_create_formatter(self):
        """测试格式化器创建"""
        from chinese_signal_formatter import create_formatter
        
        formatter = create_formatter()
        self.assertIsInstance(formatter, ChineseSignalFormatter)
        
        # 测试新实例的功能
        result = formatter.format_signal(self.complete_signal)
        self.assertIn("BCH/USDT永续合约信号", result)
        self.assertIn("做多", result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_telegram_sender_integration(self):
        """测试与Telegram发送器的集成"""
        try:
            from telegram_sender import TelegramSender
            
            # 创建模拟发送器（不实际发送消息）
            sender = TelegramSender("test_token", "@test_channel")
            
            # 测试信号数据
            test_signal = {
                "symbol": "BTC/USDT",
                "signal": "BUY",
                "entry_price": "$45000",
                "stop_loss": "$44000",
                "take_profit": "$47000",
                "confidence": "80%",
                "risk_reward_ratio": "1:2.5",
                "timeframe": "1h",
                "market_condition": "Support test",
                "indicators": {
                    "rsi": "42",
                    "macd": "Bullish crossover"
                }
            }
            
            # 测试格式化
            formatted_message = sender._format_trading_signal(test_signal)
            
            # 验证中文格式（注意HTML格式）
            self.assertIn("BTC/USDT永续合约信号", formatted_message)
            self.assertIn("做多", formatted_message)
            self.assertIn("入场价</b>：$45000", formatted_message)
            self.assertIn("止损价</b>：$44000", formatted_message)
            self.assertIn("止盈价</b>：$47000", formatted_message)
            self.assertIn("金叉", formatted_message)  # MACD翻译
            self.assertIn("支撑位测试", formatted_message)  # 市场状况翻译
            
        except ImportError:
            self.skipTest("Telegram sender not available")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试用例
    suite.addTest(loader.loadTestsFromTestCase(TestChineseSignalFormatter))
    suite.addTest(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 开始中文信号格式化器测试...")
    print("=" * 60)
    
    success = run_tests()
    
    print("=" * 60)
    if success:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 测试失败！")
        sys.exit(1)