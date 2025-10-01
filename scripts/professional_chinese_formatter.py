#!/usr/bin/env python3
"""
专业中文合约策略分析格式化器
严格遵循指定的专业格式模板
"""

from typing import Dict, Any
from datetime import datetime, timezone

class ProfessionalChineseFormatter:
    """专业中文合约策略分析格式化器"""
    
    def format_contract_analysis(self, signal: Dict[str, Any]) -> str:
        """
        格式化为专业合约策略分析格式
        
        模板：
        合约策略分析
        
        代币：BNB
        日期：2025-09-23
        
        MCP阶段与理由：分布阶段转下跌，RSI 72（超买），MACD死叉，成交量萎缩。
        
        方向：做空
        
        入场价：585附近（理由：基于24h高点-0.7%缓冲）
        
        止损价：602（风险计算：200美元/0.3 BNB=667美元距离-65美元缓冲调整）
        
        止盈价：510（目标：风险回报比1:2，基于斐波161.8%扩展）
        
        潜在风险：Binance生态新闻可能引发反弹。
        """
        
        # 提取基础数据
        symbol = signal.get('symbol', 'Unknown').replace('/USDT', '')
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        signal_direction = signal.get('signal', 'HOLD')
        
        # 价格数据
        entry_price = signal.get('entry_price', 'N/A').replace('$', '')
        stop_loss = signal.get('stop_loss', 'N/A').replace('$', '')
        take_profit = signal.get('take_profit', 'N/A').replace('$', '')
        
        # AI分析数据
        mcp_analysis = signal.get('mcp_analysis', '')
        risk_warning = signal.get('risk_warning', '')
        
        # 方向映射
        direction_map = {
            'BUY': '做多',
            'SELL': '做空', 
            'HOLD': '观望'
        }
        direction = direction_map.get(signal_direction, '观望')
        
        # 构建专业格式
        lines = []
        lines.append("合约策略分析")
        lines.append("")
        lines.append(f"代币：{symbol}")
        lines.append(f"日期：{current_date}")
        lines.append("")
        
        # MCP阶段与理由
        if mcp_analysis:
            lines.append(f"MCP阶段与理由：{mcp_analysis}")
        else:
            # 如果没有MCP分析，从技术指标生成
            indicators = signal.get('indicators', {})
            rsi = indicators.get('rsi', 'N/A')
            macd = indicators.get('macd', 'N/A')
            volume = indicators.get('volume', 'N/A')
            
            mcp_reason = f"RSI {rsi}"
            if macd != 'N/A':
                mcp_reason += f"，MACD{macd}"
            if volume != 'N/A':
                mcp_reason += f"，成交量{volume}"
            lines.append(f"MCP阶段与理由：{mcp_reason}")
        
        lines.append("")
        lines.append(f"方向：{direction}")
        lines.append("")
        
        # 入场价及理由
        if direction == '做多':
            entry_reason = "基于24h低点+0.8%缓冲"
        elif direction == '做空':
            entry_reason = "基于24h高点-0.7%缓冲"
        else:
            entry_reason = "基于当前价格"
            
        if entry_price != 'N/A':
            lines.append(f"入场价：{entry_price}附近（理由：{entry_reason}）")
        else:
            lines.append(f"入场价：{entry_price}（理由：{entry_reason}）")
        
        lines.append("")
        
        # 止损价及风险计算
        if stop_loss != 'N/A':
            # 简化的风险计算
            try:
                entry_val = float(entry_price.replace(',', ''))
                stop_val = float(stop_loss.replace(',', ''))
                risk_distance = abs(entry_val - stop_val)
                
                if direction == '做多':
                    risk_calc = f"风险计算：{risk_distance:.0f}美元距离+缓冲保护"
                else:
                    risk_calc = f"风险计算：{risk_distance:.0f}美元距离+缓冲保护"
                    
                lines.append(f"止损价：{stop_loss}（{risk_calc}）")
            except:
                lines.append(f"止损价：{stop_loss}（风险计算：基于技术分析）")
        else:
            lines.append(f"止损价：{stop_loss}")
        
        lines.append("")
        
        # 止盈价及目标
        if take_profit != 'N/A':
            risk_reward = signal.get('risk_reward_ratio', '1:2')
            lines.append(f"止盈价：{take_profit}（目标：风险回报比{risk_reward}，基于技术分析）")
        else:
            lines.append(f"止盈价：{take_profit}")
        
        lines.append("")
        
        # 潜在风险
        if risk_warning:
            lines.append(f"潜在风险：{risk_warning}")
        else:
            # 根据币种提供通用风险
            if symbol == 'BTC':
                lines.append("潜在风险：BTC联动回调或监管政策变化")
            elif symbol == 'ETH':
                lines.append("潜在风险：ETH生态系统变化或技术升级影响")
            elif symbol == 'BNB':
                lines.append("潜在风险：Binance生态新闻或监管变化")
            elif symbol == 'SOL':
                lines.append("潜在风险：Solana网络技术问题或生态系统变化")
            elif symbol == 'BCH':
                lines.append("潜在风险：比特币分叉相关新闻或市场情绪变化")
            else:
                lines.append("潜在风险：市场波动加剧或突发新闻影响")
        
        return "\n".join(lines)
    
    def format_simple_chinese(self, signal: Dict[str, Any]) -> str:
        """格式化为简化的中文信号（备用格式）"""
        symbol = signal.get('symbol', 'Unknown').replace('/USDT', '')
        signal_type = signal.get('signal', 'HOLD')
        
        # 方向映射
        direction_map = {
            'BUY': '买入',
            'SELL': '卖出',
            'HOLD': '观望'
        }
        direction = direction_map.get(signal_type, '观望')
        
        # 标题
        if signal_type == 'BUY':
            title = f"📈 【买入信号】{symbol}"
        elif signal_type == 'SELL':
            title = f"📉 【卖出信号】{symbol}"
        else:
            title = f"⏸️ 【观望建议】{symbol}"
        
        lines = [title, ""]
        
        # 核心参数
        lines.append(f"💰 入场价格: {signal.get('entry_price', 'N/A')}")
        lines.append(f"🛑 止损设置: {signal.get('stop_loss', 'N/A')}")
        lines.append(f"🎯 止盈目标: {signal.get('take_profit', 'N/A')}")
        lines.append(f"✨ 置信度: {signal.get('confidence', 'N/A')}")
        lines.append(f"⚖️ 风险回报比: {signal.get('risk_reward_ratio', 'N/A')}")
        lines.append(f"⏰ 时间框架: {signal.get('timeframe', 'N/A')}")
        lines.append("")
        
        # 技术指标
        indicators = signal.get('indicators', {})
        if indicators:
            lines.append("📊 技术分析:")
            lines.append(f"  • RSI指标: {indicators.get('rsi', 'N/A')}")
            lines.append(f"  • MACD信号: {indicators.get('macd', 'N/A')}")
            lines.append(f"  • 成交量: {indicators.get('volume', 'N/A')}")
            lines.append(f"  • 均线状态: {indicators.get('moving_averages', 'N/A')}")
            lines.append("")
        
        # 市场状况
        lines.append(f"📝 市场状况: {signal.get('market_condition', 'N/A')}")
        lines.append("")
        lines.append("⚠️ 风险提示:")
        lines.append("数字货币交易存在高风险，请合理控制仓位，设置止损，谨慎投资。以上分析仅供参考，不构成投资建议。")
        
        return "\n".join(lines)

def main():
    """测试专业格式化器"""
    
    # 示例AI信号（包含您要求的所有字段）
    sample_ai_signal = {
        "symbol": "BNB/USDT",
        "signal": "SELL",
        "current_price": "$1,008.00",
        "entry_price": "$1,008.00",
        "stop_loss": "$1,038.24",
        "take_profit": "$932.40",
        "confidence": "75%",
        "timestamp": "2025-10-01 12:18:22 UTC",
        "timeframe": "4h",
        "market_condition": "AI Analyzed",
        "risk_reward_ratio": "1:2.5",
        "indicators": {
            "rsi": "49.96",
            "macd": "接近零轴",
            "volume": "稳定",
            "moving_averages": "中性"
        },
        "price_source": "ai_realtime",
        "ai_analysis": "完整AI分析文本",
        "mcp_analysis": "分布阶段转下跌，RSI 72（超买），MACD死叉，成交量萎缩",
        "risk_warning": "Binance生态新闻可能引发反弹",
        "market_data": {
            "symbol": "BNB/USDT",
            "current_price": 1008.00,
            "high_24h": 1025.50,
            "low_24h": 985.20,
            "volume_24h": 1250000.50,
            "price_change_24h": -15.30,
            "price_change_percent_24h": -1.49,
            "data_source": "Bitget"
        }
    }
    
    formatter = ProfessionalChineseFormatter()
    
    print("=== 专业合约策略分析格式 ===")
    professional_format = formatter.format_contract_analysis(sample_ai_signal)
    print(professional_format)
    
    print("\n" + "="*60)
    print("\n=== 简化中文格式 ===")
    simple_format = formatter.format_simple_chinese(sample_ai_signal)
    print(simple_format)

if __name__ == "__main__":
    main()