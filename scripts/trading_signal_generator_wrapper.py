#!/usr/bin/env python3
"""
交易信号生成器包装器
提供向后兼容的接口，支持AI和传统信号生成
遵循KISS原则，保持简单兼容
"""

import logging
import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 导入两种信号生成器
from trading_signal_generator import TradingSignalGenerator as LegacyGenerator
from ai_trading_signal_generator import AITradingSignalGenerator as AIGenerator

logger = logging.getLogger(__name__)


class TradingSignalGeneratorWrapper:
    """交易信号生成器包装器 - 提供统一的接口"""
    
    def __init__(self, use_ai: bool = True):
        """初始化包装器
        
        Args:
            use_ai: 是否使用AI信号生成器，默认为True
        """
        self.use_ai = use_ai
        self.generator = None
        self._initialize_generator()
    
    def _initialize_generator(self):
        """初始化底层的信号生成器"""
        try:
            if self.use_ai:
                logger.info("初始化AI交易信号生成器...")
                self.generator = AIGenerator()
                logger.info("✅ AI交易信号生成器初始化成功")
            else:
                logger.info("初始化传统交易信号生成器...")
                self.generator = LegacyGenerator()
                logger.info("✅ 传统交易信号生成器初始化成功")
                
        except Exception as e:
            logger.error(f"信号生成器初始化失败: {e}")
            
            # 如果AI生成器失败，回退到传统生成器
            if self.use_ai:
                logger.warning("AI生成器初始化失败，尝试回退到传统生成器...")
                try:
                    self.use_ai = False
                    self.generator = LegacyGenerator()
                    logger.info("✅ 成功回退到传统信号生成器")
                except Exception as fallback_error:
                    logger.error(f"回退生成器也失败: {fallback_error}")
                    raise RuntimeError("所有信号生成器都不可用")
            else:
                raise RuntimeError(f"传统信号生成器初始化失败: {e}")
    
    def generate_signals(self, count: int = 3) -> List[Dict[str, Any]]:
        """生成交易信号 - 统一的接口
        
        Args:
            count: 要生成的信号数量
            
        Returns:
            交易信号列表
            
        Raises:
            RuntimeError: 当信号生成失败时
        """
        try:
            logger.info(f"开始生成 {count} 个交易信号 (AI模式: {self.use_ai})...")
            
            signals = self.generator.generate_signals(count)
            
            # 统一信号格式，确保兼容性
            unified_signals = self._unify_signal_format(signals)
            
            logger.info(f"✅ 成功生成 {len(unified_signals)} 个交易信号")
            return unified_signals
            
        except Exception as e:
            logger.error(f"信号生成失败: {e}")
            raise RuntimeError(f"交易信号生成失败: {e}")
    
    def _unify_signal_format(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """统一信号格式，确保向后兼容
        
        Args:
            signals: 原始信号列表
            
        Returns:
            统一格式的信号列表
        """
        unified_signals = []
        
        for signal in signals:
            # 创建统一格式的信号
            unified_signal = {
                # 基础字段（两种生成器都有）
                "symbol": signal.get("symbol", ""),
                "signal": signal.get("signal", ""),
                "current_price": signal.get("current_price", ""),
                "entry_price": signal.get("entry_price", ""),
                "stop_loss": signal.get("stop_loss", ""),
                "take_profit": signal.get("take_profit", ""),
                "confidence": signal.get("confidence", "75%"),
                "timestamp": signal.get("timestamp", ""),
                "timeframe": signal.get("timeframe", "4h"),
                "market_condition": signal.get("market_condition", "Analyzed"),
                "risk_reward_ratio": signal.get("risk_reward_ratio", "1:2.5"),
                "indicators": signal.get("indicators", {
                    "rsi": "Analyzed",
                    "macd": "Analyzed",
                    "volume": "Real-time",
                    "moving_averages": "Analyzed"
                }),
                "price_source": signal.get("price_source", "realtime"),
                
                # AI特有的字段（如果有）
                "ai_analysis": signal.get("ai_analysis", ""),
                "mcp_analysis": signal.get("mcp_analysis", ""),
                "risk_warning": signal.get("risk_warning", ""),
                "market_data": signal.get("market_data", {}),
                
                # 兼容性字段
                "analysis_type": "AI Expert" if self.use_ai else "Technical Analysis",
                "data_source": "Bitget + AI Model" if self.use_ai else "Bitget + Technical"
            }
            
            unified_signals.append(unified_signal)
        
        return unified_signals
    
    def get_generator_info(self) -> Dict[str, Any]:
        """获取生成器信息
        
        Returns:
            生成器信息字典
        """
        info = {
            "generator_type": "AI" if self.use_ai else "Traditional",
            "data_source": "Bitget",
            "supported_symbols": self.generator.symbols if hasattr(self.generator, 'symbols') else [],
            "features": [
                "Real-time market data",
                "Professional analysis" if self.use_ai else "Technical indicators",
                "Risk management",
                "Risk-reward optimization"
            ]
        }
        
        # 添加AI特有的信息
        if self.use_ai and hasattr(self.generator, 'expert_prompt'):
            info["analysis_method"] = "AI Expert System"
            info["prompt_source"] = "加密货币合约专家.md"
        
        return info
    
    def generate_market_summary(self) -> Dict[str, Any]:
        """生成市场摘要
        
        Returns:
            市场摘要字典
        """
        if hasattr(self.generator, 'generate_market_summary'):
            return self.generator.generate_market_summary()
        else:
            # 默认市场摘要
            from datetime import datetime, timezone
            return {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                "generator_type": "AI" if self.use_ai else "Traditional",
                "data_source": "Bitget",
                "analysis_method": "AI Expert Analysis" if self.use_ai else "Technical Analysis"
            }


def main():
    """CLI接口 - 向后兼容"""
    parser = argparse.ArgumentParser(description="Generate cryptocurrency trading signals with AI")
    parser.add_argument("--count", type=int, default=3, help="Number of signals to generate")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["json", "pretty"], default="json", help="Output format")
    parser.add_argument("--include-summary", action="store_true", help="Include market summary")
    parser.add_argument("--use-ai", action="store_true", default=True, help="Use AI signal generator (default: True)")
    parser.add_argument("--use-traditional", action="store_true", help="Use traditional signal generator instead of AI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--info", action="store_true", help="Show generator information")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 确定使用哪种生成器
    use_ai = args.use_ai and not args.use_traditional
    
    try:
        # 创建包装器
        wrapper = TradingSignalGeneratorWrapper(use_ai=use_ai)
        
        # 如果请求信息，显示生成器信息并退出
        if args.info:
            info = wrapper.get_generator_info()
            print(json.dumps(info, indent=2, ensure_ascii=False))
            return 0
        
        logger.info(f"使用{'AI' if use_ai else '传统'}信号生成器")
        
        # 生成信号
        signals = wrapper.generate_signals(args.count)
        
        # 构建输出
        output = {
            "signals": signals,
            "generated_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            "total_signals": len(signals),
            "generator_info": wrapper.get_generator_info()
        }
        
        if args.include_summary:
            output["market_summary"] = wrapper.generate_market_summary()
        
        # 格式化输出
        if args.format == "json":
            result = json.dumps(output, indent=2, ensure_ascii=False)
        else:
            result = format_unified_signals_pretty(output)
        
        # 输出结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Generated {len(signals)} signals to {args.output}")
        else:
            print(result)
            
    except RuntimeError as e:
        logger.error(f"❌ 信号生成失败: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ 意外错误: {e}")
        return 1
    
    return 0


def format_unified_signals_pretty(data: Dict[str, Any]) -> str:
    """格式化统一的信号输出"""
    lines = []
    
    # 头部信息
    generator_info = data.get("generator_info", {})
    generator_type = generator_info.get("generator_type", "Unknown")
    
    if generator_type == "AI":
        lines.append("🤖 AI智能交易信号")
    else:
        lines.append("📊 传统技术分析信号")
    
    lines.append(f"生成时间: {data['generated_at']}")
    lines.append(f"数据来源: {generator_info.get('data_source', 'Unknown')}")
    lines.append(f"信号数量: {data['total_signals']}")
    lines.append("")
    
    # 市场摘要（如果有）
    if "market_summary" in data:
        summary = data["market_summary"]
        lines.append("📊 市场摘要")
        for key, value in summary.items():
            if key not in ["market_summary"]:
                lines.append(f"  {key}: {value}")
        lines.append("")
    
    # 信号详情
    lines.append("🎯 交易信号")
    lines.append("")
    
    for i, signal in enumerate(data["signals"], 1):
        lines.append(f"信号 #{i} - {signal['symbol']}")
        lines.append(f"  📈 方向: {signal['signal']}")
        lines.append(f"  💰 当前价格: {signal['current_price']}")
        lines.append(f"  🚪 入场价格: {signal['entry_price']}")
        lines.append(f"  🛑 止损价格: {signal['stop_loss']}")
        lines.append(f"  🎯 止盈价格: {signal['take_profit']}")
        lines.append(f"  📊 置信度: {signal['confidence']}")
        lines.append(f"  ⚖️ 风险回报: {signal['risk_reward_ratio']}")
        lines.append(f"  ⏰ 时间框架: {signal['timeframe']}")
        lines.append(f"  🔍 价格来源: {signal['price_source']}")
        lines.append(f"  🔬 分析类型: {signal['analysis_type']}")
        
        # AI特有的字段
        if signal.get("mcp_analysis"):
            lines.append(f"  📋 MCP分析: {signal['mcp_analysis']}")
        
        if signal.get("risk_warning"):
            lines.append(f"  ⚠️ 风险提醒: {signal['risk_warning']}")
        
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    exit(main())