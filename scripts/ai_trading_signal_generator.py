#!/usr/bin/env python3
"""
AI驱动的交易信号生成器
基于专家提示词和实时市场数据生成专业的加密货币交易信号
遵循KISS原则，高内聚低耦合设计
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from bitget_client import BitgetClient, BitgetPriceData
from openai_client import create_openai_client
from notification_service import notify_realtime_data_failure

logger = logging.getLogger(__name__)


class AITradingSignalGenerator:
    """AI驱动的专业交易信号生成器"""
    
    def __init__(self):
        """初始化生成器 - KISS原则：只依赖必要的组件"""
        self.symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "BCH/USDT"]
        self.bitget_client = BitgetClient()
        self.openai_client = None
        self.expert_prompt = None
        self._load_expert_prompt()
        self._initialize_ai_client()
    
    def _load_expert_prompt(self) -> None:
        """加载专家提示词 - 高内聚：单一职责"""
        try:
            prompt_file = script_dir.parent / '加密货币合约专家.md'
            if not prompt_file.exists():
                raise FileNotFoundError(f"专家提示词文件未找到: {prompt_file}")
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                self.expert_prompt = f.read()
            
            logger.info(f"✅ 成功加载专家提示词: {len(self.expert_prompt)} 字符")
            
        except Exception as e:
            logger.error(f"加载专家提示词失败: {e}")
            raise RuntimeError(f"无法加载专家提示词: {e}")
    
    def _initialize_ai_client(self) -> None:
        """初始化AI客户端 - 低耦合：通过工厂函数创建"""
        try:
            self.openai_client = create_openai_client()
            if not self.openai_client:
                raise RuntimeError("AI客户端初始化失败 - API密钥未配置")
            
            logger.info("✅ AI客户端初始化成功")
            
        except Exception as e:
            logger.error(f"AI客户端初始化失败: {e}")
            raise RuntimeError(f"AI客户端不可用: {e}")
    
    def generate_signals(self, count: int = 3) -> List[Dict[str, Any]]:
        """生成AI驱动的专业交易信号
        
        Args:
            count: 要生成的信号数量
            
        Returns:
            交易信号列表
            
        Raises:
            RuntimeError: 当实时数据或AI分析失败时
        """
        if count <= 0:
            return []
        
        logger.info(f"开始生成 {count} 个AI驱动的交易信号...")
        
        # 随机选择指定数量的币种
        import random
        selected_symbols = random.sample(self.symbols, min(count, len(self.symbols)))
        
        signals = []
        for symbol in selected_symbols:
            try:
                signal = self._generate_ai_signal(symbol)
                signals.append(signal)
                logger.info(f"✅ 成功生成 {symbol} 的AI交易信号")
            except RuntimeError as e:
                logger.error(f"❌ 生成 {symbol} 的AI信号失败: {e}")
                raise  # 重新抛出，让上层处理
        
        logger.info(f"🎉 成功生成 {len(signals)} 个AI交易信号")
        return signals
    
    def _generate_ai_signal(self, symbol: str) -> Dict[str, Any]:
        """为单个币种生成AI驱动的交易信号
        
        Args:
            symbol: 交易对符号 (如 'BTC/USDT')
            
        Returns:
            AI生成的交易信号
            
        Raises:
            RuntimeError: 当数据获取或AI分析失败时
        """
        try:
            logger.info(f"开始为 {symbol} 生成AI交易信号...")
            
            # 1. 获取实时市场数据
            market_data = self._get_market_data(symbol)
            if not market_data:
                raise RuntimeError(f"无法获取 {symbol} 的市场数据")
            
            # 2. 构建AI提示词
            ai_prompt = self._build_ai_prompt(symbol, market_data)
            
            # 3. 调用AI生成专业分析
            logger.info(f"正在调用AI分析 {symbol}...")
            ai_response = self._call_ai_analysis(ai_prompt)
            
            if not ai_response:
                raise RuntimeError(f"AI分析 {symbol} 失败")
            
            # 4. 解析AI响应为结构化信号
            signal = self._parse_ai_signal(symbol, market_data, ai_response)
            
            logger.info(f"✅ 成功解析 {symbol} 的AI信号")
            return signal
            
        except RuntimeError:
            raise  # 重新抛出RuntimeError
        except Exception as e:
            error_msg = f"生成 {symbol} 的AI信号失败: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取实时市场数据 - 高内聚：单一数据源"""
        try:
            base_symbol = symbol.replace('/USDT', '')
            ticker_data = self.bitget_client.get_ticker(base_symbol)
            
            if not ticker_data:
                logger.warning(f"无法获取 {symbol} 的Bitget数据")
                return None
            
            # 构建标准化的市场数据结构
            market_data = {
                "symbol": symbol,
                "current_price": ticker_data.price,
                "high_24h": ticker_data.high_24h,
                "low_24h": ticker_data.low_24h,
                "volume_24h": ticker_data.volume_24h,
                "price_change_24h": ticker_data.price_change_24h,
                "price_change_percent_24h": ticker_data.price_change_percent_24h,
                "data_source": ticker_data.data_source,
                "last_update": ticker_data.last_update.isoformat() if hasattr(ticker_data.last_update, 'isoformat') else str(ticker_data.last_update),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ 获取 {symbol} 市场数据: ${market_data['current_price']:,.2f}")
            return market_data
            
        except Exception as e:
            logger.error(f"获取 {symbol} 市场数据失败: {e}")
            
            # 通知用户数据获取失败
            notify_realtime_data_failure(symbol, str(e), {
                "function": "_get_market_data",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            })
            
            return None
    
    def _build_ai_prompt(self, symbol: str, market_data: Dict[str, Any]) -> str:
        """构建AI分析提示词 - 专业格式"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now(timezone.utc).strftime('%H:%M:%S UTC')
        
        # 替换专家提示词中的占位符
        prompt = self.expert_prompt.replace('HYPE', symbol.replace('/USDT', ''))
        prompt = prompt.replace('2025-09-23', current_date)
        prompt = prompt.replace('当前日期：2025-09-23', f'当前日期：{current_date}')
        prompt = prompt.replace('当前日期: 2025-09-23', f'当前日期: {current_date}')
        
        # 添加实时市场数据上下文
        market_context = f"""
=== 实时市场数据 (来源: {market_data['data_source']}, 更新时间: {current_time}) ===

**当前价格**: ${market_data['current_price']:,.2f}
**24小时变化**: {market_data['price_change_percent_24h']:+.2f}% (${market_data['price_change_24h']:+.2f})
**24小时最高价**: ${market_data['high_24h']:,.2f}
**24小时最低价**: ${market_data['low_24h']:,.2f}
**24小时成交量**: ${market_data['volume_24h']:,.0f}

=== 分析要求 ===

基于上述实时数据，严格按照专家提示词格式生成交易信号。
所有价格计算必须使用实时数据，禁止编造价格。
输出格式必须严格遵守模板要求。

"""
        
        return market_context + prompt
    
    def _call_ai_analysis(self, prompt: str) -> Optional[str]:
        """调用AI进行分析 - 低耦合：通过统一接口"""
        try:
            logger.info("正在调用AI进行分析...")
            
            response = self.openai_client.chat_completions_create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.1,  # 降低随机性，确保专业性
                max_tokens=1500,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                analysis = response.choices[0].message.content.strip()
                logger.info(f"✅ AI分析完成，长度: {len(analysis)} 字符")
                return analysis
            else:
                logger.error("AI响应格式异常")
                return None
                
        except Exception as e:
            logger.error(f"AI分析调用失败: {e}")
            return None
    
    def _parse_ai_signal(self, symbol: str, market_data: Dict[str, Any], ai_response: str) -> Dict[str, Any]:
        """解析AI响应为结构化信号 - KISS原则：简单直接的解析"""
        try:
            logger.info(f"正在解析 {symbol} 的AI响应...")
            
            # 提取关键信息
            signal_data = {
                "symbol": symbol,
                "current_price": f"${market_data['current_price']:,.2f}",
                "price_source": "ai_realtime",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "data_source": market_data['data_source'],
                "ai_analysis": ai_response,
                "market_data": market_data
            }
            
            # 简单的关键词解析（KISS原则）
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 解析方向
                if "方向：" in line:
                    direction = line.split("方向：")[-1].strip()
                    signal_data["signal"] = self._normalize_direction(direction)
                
                # 解析入场价
                elif "入场价：" in line and "$" in line:
                    entry_price = self._extract_price(line)
                    if entry_price:
                        signal_data["entry_price"] = f"${entry_price:,.2f}"
                
                # 解析止损价
                elif "止损价：" in line and "$" in line:
                    stop_loss = self._extract_price(line)
                    if stop_loss:
                        signal_data["stop_loss"] = f"${stop_loss:,.2f}"
                
                # 解析止盈价
                elif "止盈价：" in line and "$" in line:
                    take_profit = self._extract_price(line)
                    if take_profit:
                        signal_data["take_profit"] = f"${take_profit:,.2f}"
                
                # 解析MCP分析
                elif "MCP阶段与理由：" in line:
                    signal_data["mcp_analysis"] = line.split("MCP阶段与理由：")[-1].strip()
                
                # 解析风险
                elif "潜在风险：" in line:
                    signal_data["risk_warning"] = line.split("潜在风险：")[-1].strip()
            
            # 补充缺失的字段
            self._fill_missing_fields(signal_data, market_data)
            
            logger.info(f"✅ 成功解析 {symbol} 的信号数据")
            return signal_data
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            raise RuntimeError(f"无法解析AI分析结果: {e}")
    
    def _normalize_direction(self, direction: str) -> str:
        """标准化方向字符串"""
        direction = direction.upper()
        if "多" in direction or "BUY" in direction:
            return "BUY"
        elif "空" in direction or "SELL" in direction:
            return "SELL"
        elif "观望" in direction or "HOLD" in direction:
            return "HOLD"
        else:
            return "HOLD"  # 默认观望
    
    def _extract_price(self, line: str) -> Optional[float]:
        """从文本行中提取价格"""
        import re
        # 查找$符号后的数字
        match = re.search(r'\$(\d+(?:\.\d+)?)', line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def _fill_missing_fields(self, signal_data: Dict[str, Any], market_data: Dict[str, Any]) -> None:
        """填充缺失的字段，确保数据完整性"""
        current_price = market_data['current_price']
        
        # 如果AI没有提供某些字段，使用合理的默认值
        if "signal" not in signal_data:
            signal_data["signal"] = "HOLD"
        
        if "entry_price" not in signal_data:
            signal_data["entry_price"] = f"${current_price:,.2f}"
        
        if "stop_loss" not in signal_data:
            # 默认3%止损
            stop_loss = current_price * 0.97 if signal_data["signal"] == "BUY" else current_price * 1.03
            signal_data["stop_loss"] = f"${stop_loss:,.2f}"
        
        if "take_profit" not in signal_data:
            # 默认1:2.5风险回报比
            entry_price = float(signal_data["entry_price"].replace('$', '').replace(',', ''))
            stop_price = float(signal_data["stop_loss"].replace('$', '').replace(',', ''))
            
            if signal_data["signal"] == "BUY":
                risk = abs(entry_price - stop_price)
                reward = risk * 2.5
                take_profit = entry_price + reward
            else:
                risk = abs(stop_price - entry_price)
                reward = risk * 2.5
                take_profit = entry_price - reward
            
            signal_data["take_profit"] = f"${take_profit:,.2f}"
        
        # 添加技术指标（基于AI分析或默认值）
        if "confidence" not in signal_data:
            signal_data["confidence"] = "75%"  # AI分析的默认置信度
        
        if "timeframe" not in signal_data:
            signal_data["timeframe"] = "4h"  # 默认时间框架
        
        if "risk_reward_ratio" not in signal_data:
            signal_data["risk_reward_ratio"] = "1:2.5"  # 默认风险回报比
        
        if "market_condition" not in signal_data:
            signal_data["market_condition"] = "AI Analyzed"
        
        if "indicators" not in signal_data:
            signal_data["indicators"] = {
                "rsi": "AI Generated",
                "macd": "AI Generated", 
                "volume": "Real-time Data",
                "moving_averages": "AI Analysis"
            }
    
    def generate_market_summary(self) -> Dict[str, Any]:
        """生成AI驱动的市场摘要"""
        return {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            "analysis_type": "AI Expert Analysis",
            "data_source": "Bitget + AI Model",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


def main():
    """CLI接口 - 保持向后兼容"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AI-powered cryptocurrency trading signals")
    parser.add_argument("--count", type=int, default=3, help="Number of signals to generate")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["json", "pretty"], default="json", help="Output format")
    parser.add_argument("--include-summary", action="store_true", help="Include market summary")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    generator = AITradingSignalGenerator()
    
    try:
        signals = generator.generate_signals(args.count)
        
        output = {
            "signals": signals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_signals": len(signals),
            "analysis_type": "AI Expert Analysis",
            "data_source": "Bitget + AI Model"
        }
        
        if args.include_summary:
            output["market_summary"] = generator.generate_market_summary()
        
        if args.format == "json":
            result = json.dumps(output, indent=2, ensure_ascii=False)
        else:
            result = format_ai_signals_pretty(output)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Generated {len(signals)} AI signals to {args.output}")
        else:
            print(result)
            
    except RuntimeError as e:
        logger.error(f"❌ AI信号生成失败: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ 意外错误: {e}")
        return 1
    
    return 0


def format_ai_signals_pretty(data: Dict[str, Any]) -> str:
    """格式化AI信号输出 - KISS原则：简单清晰"""
    lines = []
    
    # 头部信息
    lines.append("🤖 AI交易信号分析")
    lines.append(f"生成时间: {data['generated_at']}")
    lines.append(f"数据来源: {data['data_source']}")
    lines.append(f"信号数量: {data['total_signals']}")
    lines.append("")
    
    if "market_summary" in data:
        summary = data["market_summary"]
        lines.append("📊 市场摘要")
        for key, value in summary.items():
            if key != "market_summary":
                lines.append(f"  {key}: {value}")
        lines.append("")
    
    # AI信号详情
    lines.append("🎯 AI交易信号")
    lines.append("")
    
    for i, signal in enumerate(data["signals"], 1):
        lines.append(f"信号 #{i} - {signal['symbol']}")
        lines.append(f"  📈 方向: {signal['signal']}")
        lines.append(f"  💰 当前价格: {signal['current_price']}")
        lines.append(f"  🚪 入场价格: {signal['entry_price']}")
        lines.append(f"  🛑 止损价格: {signal['stop_loss']}")
        lines.append(f"  🎯 止盈价格: {signal['take_profit']}")
        lines.append(f"  📊 置信度: {signal.get('confidence', 'N/A')}")
        lines.append(f"  ⚖️ 风险回报: {signal.get('risk_reward_ratio', 'N/A')}")
        lines.append(f"  ⏰ 时间框架: {signal.get('timeframe', 'N/A')}")
        lines.append(f"  🔍 价格来源: {signal['price_source']}")
        
        if "mcp_analysis" in signal:
            lines.append(f"  📋 MCP分析: {signal['mcp_analysis']}")
        
        if "risk_warning" in signal:
            lines.append(f"  ⚠️ 风险提醒: {signal['risk_warning']}")
        
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    exit(main())