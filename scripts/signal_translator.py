#!/usr/bin/env python3
"""
交易信号中文翻译器
将英文交易信号翻译成专业的中文版本
"""

import json
from typing import Dict, Any

class SignalTranslator:
    """交易信号翻译器"""
    
    def __init__(self):
        # 信号类型翻译
        self.signal_translations = {
            "BUY": "买入",
            "SELL": "卖出", 
            "HOLD": "观望"
        }
        
        # 市场条件翻译
        self.condition_translations = {
            "Support test": "支撑位测试",
            "Resistance test": "阻力位测试",
            "Breakout potential": "突破潜力",
            "Trending down": "下跌趋势",
            "Trending up": "上涨趋势",
            "Sideways": "横盘整理",
            "Volatile": "高波动性",
            "Consolidating": "盘整阶段",
            "Mixed signals": "信号混杂",
            "Death cross": "死亡交叉",
            "Golden cross": "黄金交叉",
            "Bullish crossover": "看涨交叉",
            "Bearish crossover": "看跌交叉",
            "Signal line crossover": "信号线交叉",
            "Neutral": "中性"
        }
        
        # 技术指标翻译
        self.indicator_translations = {
            "RSI": "RSI指标",
            "MACD": "MACD指标",
            "Volume": "成交量",
            "moving_averages": "移动平均线"
        }
        
        # 市场情绪翻译
        self.sentiment_translations = {
            "Bullish": "看涨",
            "Bearish": "看跌", 
            "Neutral": "中性"
        }
        
    def translate_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """翻译单个交易信号"""
        
        # 基础信息翻译
        translated = {
            "交易对": signal.get('symbol', ''),
            "信号": self.signal_translations.get(signal.get('signal', ''), signal.get('signal', '')),
            "入场价格": signal.get('entry_price', ''),
            "止损价格": signal.get('stop_loss', ''),
            "止盈价格": signal.get('take_profit', ''),
            "置信度": signal.get('confidence', ''),
            "风险回报比": signal.get('risk_reward_ratio', ''),
            "时间框架": signal.get('timeframe', ''),
            "市场状况": self.condition_translations.get(signal.get('market_condition', ''), signal.get('market_condition', '')),
            "时间戳": signal.get('timestamp', '')
        }
        
        # 技术指标翻译
        if 'indicators' in signal:
            indicators = signal['indicators']
            translated["技术指标"] = {
                "RSI": indicators.get('rsi', ''),
                "MACD": self.condition_translations.get(indicators.get('macd', ''), indicators.get('macd', '')),
                "成交量": indicators.get('volume', ''),
                "移动平均线": self.condition_translations.get(indicators.get('moving_averages', ''), indicators.get('moving_averages', ''))
            }
        
        return translated
    
    def format_professional_chinese(self, signal: Dict[str, Any]) -> str:
        """格式化为专业的中文信号格式"""
        
        # 获取翻译后的信号
        translated = self.translate_signal(signal)
        
        # 构建专业格式
        message_parts = []
        
        # 标题部分
        signal_type = translated["信号"]
        symbol = translated["交易对"]
        
        if signal_type == "买入":
            title = f"📈 【买入信号】{symbol}"
        elif signal_type == "卖出":
            title = f"📉 【卖出信号】{symbol}"
        else:
            title = f"⏸️ 【观望建议】{symbol}"
            
        message_parts.append(title)
        message_parts.append("")  # 空行
        
        # 核心参数部分
        message_parts.append(f"💰 入场价格: {translated['入场价格']}")
        message_parts.append(f"🛑 止损设置: {translated['止损价格']}")
        message_parts.append(f"🎯 止盈目标: {translated['止盈价格']}")
        message_parts.append(f"✨ 置信度: {translated['置信度']}")
        message_parts.append(f"⚖️ 风险回报比: {translated['风险回报比']}")
        message_parts.append(f"⏰ 时间框架: {translated['时间框架']}")
        message_parts.append("")  # 空行
        
        # 技术指标部分
        if '技术指标' in translated:
            message_parts.append("📊 技术分析:")
            indicators = translated['技术指标']
            message_parts.append(f"  • RSI指标: {indicators['RSI']}")
            message_parts.append(f"  • MACD信号: {indicators['MACD']}")
            message_parts.append(f"  • 成交量: {indicators['成交量']}")
            message_parts.append(f"  • 均线状态: {indicators['移动平均线']}")
            message_parts.append("")  # 空行
        
        # 市场状况
        message_parts.append(f"📝 市场状况: {translated['市场状况']}")
        
        # 风险提示（专业版本必备）
        message_parts.append("")
        message_parts.append("⚠️ 风险提示:")
        message_parts.append("数字货币交易存在高风险，请合理控制仓位，设置止损，谨慎投资。以上分析仅供参考，不构成投资建议。")
        
        return "\n".join(message_parts)
    
    def translate_market_summary(self, summary: Dict[str, Any]) -> str:
        """翻译市场摘要"""
        
        parts = []
        parts.append(f"📊 【市场综述】{summary.get('date', '')} {summary.get('time', '')}")
        parts.append("")
        parts.append(f"🎯 市场情绪: {self.sentiment_translations.get(summary.get('market_sentiment', ''), summary.get('market_sentiment', ''))}")
        parts.append(f"📈 波动水平: {summary.get('volatility', '')}")
        parts.append(f"📊 主导趋势: {summary.get('dominant_trend', '')}")
        
        if 'key_levels' in summary:
            levels = summary['key_levels']
            parts.append("")
            parts.append("🔑 关键价位:")
            if 'btc_support' in levels:
                parts.append(f"  • BTC支撑位: {levels['btc_support']}")
            if 'btc_resistance' in levels:
                parts.append(f"  • BTC阻力位: {levels['btc_resistance']}")
            if 'eth_support' in levels:
                parts.append(f"  • ETH支撑位: {levels['eth_support']}")
            if 'eth_resistance' in levels:
                parts.append(f"  • ETH阻力位: {levels['eth_resistance']}")
        
        parts.append("")
        parts.append("💡 策略建议: 请结合个人风险承受能力，合理配置资金，严格执行风险管理策略。")
        
        return "\n".join(parts)

def main():
    """测试翻译功能"""
    
    # 示例信号（你提供的英文信号）
    sample_signal = {
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
    
    # 示例市场摘要
    sample_summary = {
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
    
    print("=== 原始英文信号 ===")
    print(json.dumps(sample_signal, indent=2, ensure_ascii=False))
    
    print("\n=== 专业中文翻译 ===")
    chinese_signal = translator.format_professional_chinese(sample_signal)
    print(chinese_signal)
    
    print("\n" + "="*60)
    print("=== 市场摘要翻译 ===")
    chinese_summary = translator.translate_market_summary(sample_summary)
    print(chinese_summary)

if __name__ == "__main__":
    main()