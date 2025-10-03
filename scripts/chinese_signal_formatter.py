#!/usr/bin/env python3
"""
专业中文交易信号格式化器
将英文交易信号转换为专业的中文格式
遵循KISS原则：保持简单、高内聚、低耦合
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ChineseSignalFormatter:
    """专业中文交易信号格式化器"""
    
    def __init__(self):
        """初始化格式化器"""
        self.signal_translations = {
            "BUY": "做多",
            "SELL": "做空", 
            "HOLD": "持仓观望"
        }
        
        self.condition_translations = {
            "Support test": "支撑位测试",
            "Resistance test": "阻力位测试",
            "Breakout": "突破",
            "Pullback": "回调",
            "Consolidation": "盘整",
            "Trend continuation": "趋势延续",
            "Trend reversal": "趋势反转",
            "AI Analyzed": "AI分析"
        }
        
        self.macd_translations = {
            "Bullish crossover": "金叉",
            "Bearish crossover": "死叉",
            "Positive divergence": "正背离",
            "Negative divergence": "负背离",
            "Near zero line": "接近零轴",
            "Strong bullish": "强势看涨",
            "Strong bearish": "强势看跌"
        }
    
    def format_signal(self, signal_data: Dict[str, Any]) -> str:
        """
        将交易信号数据格式化为专业中文Telegram消息
        
        Args:
            signal_data: 交易信号数据字典
            
        Returns:
            str: 格式化的中文消息
        """
        try:
            # 提取信号数据（防御性编程）
            symbol = signal_data.get("symbol", "Unknown")
            signal_type = signal_data.get("signal", "Unknown")
            entry_price = signal_data.get("entry_price", "N/A")
            stop_loss = signal_data.get("stop_loss", "N/A")
            take_profit = signal_data.get("take_profit", "N/A")
            confidence = signal_data.get("confidence", "N/A")
            risk_reward = signal_data.get("risk_reward_ratio", "N/A")
            timeframe = signal_data.get("timeframe", "N/A")
            market_condition = signal_data.get("market_condition", "N/A")
            
            # 提取技术指标
            indicators = signal_data.get("indicators", {})
            rsi = indicators.get("rsi", "N/A")
            macd = indicators.get("macd", "N/A")
            
            # 翻译关键字段
            signal_chinese = self.signal_translations.get(signal_type, signal_type)
            condition_chinese = self.condition_translations.get(market_condition, market_condition)
            macd_chinese = self.macd_translations.get(macd, macd)
            
            # 构建专业中文消息
            message = f"🎯 <b>{symbol}永续合约信号</b>\n\n"
            
            # 信号方向
            message += f"📊 <b>方向</b>：{signal_chinese}\n"
            
            # 价格信息
            message += f"💰 <b>入场价</b>：{entry_price}\n"
            message += f"🛑 <b>止损价</b>：{stop_loss}\n"
            message += f"🎯 <b>止盈价</b>：{take_profit}\n"
            
            # 风险与信心
            message += f"⚖️ <b>风险回报比</b>：{risk_reward}\n"
            message += f"📈 <b>信心度</b>：{confidence}\n"
            
            # 技术指标
            message += f"📊 <b>RSI指标</b>：{rsi}\n"
            message += f"📊 <b>MACD信号</b>：{macd_chinese}\n"
            
            # 时间框架和条件
            message += f"⏰ <b>时间框架</b>：{timeframe}\n"
            message += f"📝 <b>市场状况</b>：{condition_chinese}\n"
            
            # 风险提示
            message += "\n⚠️ <i>风险提示：交易涉及风险，请仅投资您能承受损失的资金。</i>"
            
            return message
            
        except Exception as e:
            logger.error(f"格式化交易信号时出错: {e}")
            # 出错时返回英文格式作为后备
            return self._fallback_english_format(signal_data)
    
    def _fallback_english_format(self, signal_data: Dict[str, Any]) -> str:
        """后备英文格式（当中文格式化失败时使用）"""
        # 防御性编程：处理无效数据类型
        if not isinstance(signal_data, dict):
            return """📊 <b>SmartWallex Trading Signal</b>

🪙 <b>Symbol:</b> Unknown
📈 <b>Signal:</b> Unknown
💰 <b>Entry:</b> N/A
🛑 <b>Stop Loss:</b> N/A
🎯 <b>Take Profit:</b> N/A
📊 <b>Confidence:</b> N/A
⚖️ <b>Risk/Reward:</b> N/A
📊 <b>RSI:</b> N/A | <b>MACD:</b> N/A
⏰ <b>Timeframe:</b> N/A
📝 <b>Condition:</b> N/A

⚠️ <i>Risk Warning: Trading involves risk. Only invest what you can afford to lose.</i>"""
        
        symbol = signal_data.get("symbol", "Unknown")
        signal = signal_data.get("signal", "Unknown")
        entry_price = signal_data.get("entry_price", "N/A")
        stop_loss = signal_data.get("stop_loss", "N/A")
        take_profit = signal_data.get("take_profit", "N/A")
        confidence = signal_data.get("confidence", "N/A")
        risk_reward = signal_data.get("risk_reward_ratio", "N/A")
        
        indicators = signal_data.get("indicators", {})
        rsi = indicators.get("rsi", "N/A")
        macd = indicators.get("macd", "N/A")
        timeframe = signal_data.get("timeframe", "N/A")
        condition = signal_data.get("market_condition", "N/A")
        
        return f"""📊 <b>SmartWallex Trading Signal</b>

🪙 <b>Symbol:</b> {symbol}
📈 <b>Signal:</b> {signal}
💰 <b>Entry:</b> {entry_price}
🛑 <b>Stop Loss:</b> {stop_loss}
🎯 <b>Take Profit:</b> {take_profit}
📊 <b>Confidence:</b> {confidence}
⚖️ <b>Risk/Reward:</b> {risk_reward}
📊 <b>RSI:</b> {rsi} | <b>MACD:</b> {macd}
⏰ <b>Timeframe:</b> {timeframe}
📝 <b>Condition:</b> {condition}

⚠️ <i>Risk Warning: Trading involves risk. Only invest what you can afford to lose.</i>"""


def create_formatter() -> ChineseSignalFormatter:
    """创建中文信号格式化器实例"""
    return ChineseSignalFormatter()


if __name__ == "__main__":
    # 测试格式化器
    test_signal = {
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
    
    formatter = ChineseSignalFormatter()
    result = formatter.format_signal(test_signal)
    print("测试结果：")
    print(result)