#!/usr/bin/env python3
"""
加密货币合约分析器 - 生成专业的永续合约交易信号

该模块使用AI专家提示词生成BTC, ETH, BNB, SOL, BCH五种主流
加密货币的永续合约交易信号，遵循Market Cycle Phases (MCP)分析框架。
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from openai_client import create_openai_client
from price_fetcher import PriceFetcher, PriceData
from notification_service import notify_realtime_data_failure, notify_trading_pause


class CryptoSwapAnalyzer:
    """加密货币合约分析器核心类"""
    
    # 支持的加密货币列表
    SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'BNB', 'SOL', 'BCH']
    
    def __init__(self):
        """初始化分析器"""
        self.setup_logging()
        self.openai_client = create_openai_client()
        self.expert_prompt = self._load_expert_prompt()
        self.price_fetcher = PriceFetcher()
        
    def setup_logging(self) -> None:
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(script_dir / 'crypto_swap_analyzer.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_expert_prompt(self) -> str:
        """加载专家提示词模板"""
        prompt_file = script_dir.parent / '加密货币合约专家.md'
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.info(f"成功加载专家提示词: {prompt_file}")
            return content
        except FileNotFoundError:
            self.logger.error(f"专家提示词文件未找到: {prompt_file}")
            raise
        except Exception as e:
            self.logger.error(f"加载专家提示词失败: {e}")
            raise
            
    def generate_analysis_for_crypto(self, crypto: str, current_date: str) -> str:
        """为单个加密货币生成分析 - 严格要求实时数据
        
        Args:
            crypto: 加密货币符号 (如 'BTC')
            current_date: 当前日期 (格式: 'YYYY-MM-DD')
            
        Returns:
            生成的分析内容
            
        Raises:
            RuntimeError: 当实时数据获取失败时抛出
        """
        try:
            self.logger.info(f"开始为 {crypto} 获取实时价格数据...")
            
            # 严格要求获取实时价格数据，失败时报错
            price_data = self.price_fetcher.get_realtime_price(crypto)
            
            if not price_data:
                # 这种情况不应该发生，因为get_realtime_price会抛出异常
                error_msg = f"❌ CRITICAL: 无法获取 {crypto} 实时价格数据。交易程序已暂停。"
                self.logger.error(error_msg)
                
                # 通知用户
                notify_realtime_data_failure(crypto, error_msg, {
                    "function": "generate_analysis_for_crypto",
                    "current_date": current_date,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                raise RuntimeError(error_msg)
            
            # 验证价格数据合理性
            if price_data.price <= 0:
                error_msg = f"❌ CRITICAL: {crypto} 实时价格数据异常: ${price_data.price:,.2f}。交易程序已暂停。"
                self.logger.error(error_msg)
                
                notify_realtime_data_failure(crypto, error_msg, {
                    "function": "generate_analysis_for_crypto",
                    "price_data": str(price_data),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                raise RuntimeError(error_msg)
            
            # 构建包含实时价格的提示词
            crypto_prompt = self._build_price_aware_prompt(crypto, current_date, price_data)
            
            self.logger.info(f"开始为 {crypto} 生成合约分析 (实时价格: ${price_data.price:,.2f})...")
            
            response = self.openai_client.chat_completions_create(
                messages=[{
                    "role": "user", 
                    "content": crypto_prompt
                }],
                temperature=0.3,  # 降低随机性以确保专业性
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content.strip()
            self.logger.info(f"✅ 成功生成 {crypto} 分析，长度: {len(analysis)} 字符")
            return analysis
            
        except RuntimeError:
            # 重新抛出RuntimeError，让上层处理
            raise
        except Exception as e:
            error_msg = f"生成 {crypto} 分析失败: {e}"
            self.logger.error(error_msg)
            
            # 通知用户
            notify_realtime_data_failure(crypto, error_msg, {
                "function": "generate_analysis_for_crypto",
                "current_date": current_date,
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            raise RuntimeError(error_msg)
    
    def _build_price_aware_prompt(self, crypto: str, current_date: str, price_data: PriceData) -> str:
        """构建包含实时价格的AI提示词"""
        
        # 将实时价格数据插入到专家提示词中
        price_context = f"""
=== 实时市场数据 (来源: {price_data.data_source}, 更新时间: {price_data.last_update.strftime('%Y-%m-%d %H:%M:%S UTC')}) ===

**当前价格**: ${price_data.price:,.2f}
**24小时变化**: {price_data.price_change_percent_24h:+.2f}% (${price_data.price_change_24h:+,.2f})
**24小时最高价**: ${price_data.high_24h:,.2f}
**24小时最低价**: ${price_data.low_24h:,.2f}
**24小时成交量**: ${price_data.volume_24h:,.0f}

=== 重要指令 ===

**必须严格遵守以下规则：**
1. **所有价格计算必须基于上述实时数据**
2. **入场价必须基于24小时最高/最低价进行合理缓冲设置**
3. **止损/止盈价必须基于实时价格和风险计算**
4. **绝对禁止使用任何示例价格或历史价格**
5. **如果实时数据与任何示例冲突，以实时数据为准**

**违反上述规则将导致分析无效！**

"""
        
        # 在专家提示词的开头插入价格上下文
        enhanced_prompt = price_context + self.expert_prompt
        enhanced_prompt = enhanced_prompt.replace('HYPE', crypto)
        enhanced_prompt = enhanced_prompt.replace('2025-09-23', current_date)
        
        return enhanced_prompt
    
    def _generate_ai_only_analysis(self, crypto: str, current_date: str) -> Optional[str]:
        """当无法获取实时价格时，使用纯AI分析（降级方案）"""
        try:
            self.logger.warning(f"使用AI估算为 {crypto} 生成分析（无实时价格）")
            
            # 构建不依赖实时价格的提示词
            fallback_prompt = f"""
注意：由于技术原因无法获取实时价格数据，请基于技术分析模式和合理估算生成分析。

请在分析中明确标注价格数据为估算值，并建议用户核实实际价格。

{self.expert_prompt.replace('HYPE', crypto).replace('2025-09-23', current_date)}
"""
            
            response = self.openai_client.chat_completions_create(
                messages=[{
                    "role": "user", 
                    "content": fallback_prompt
                }],
                temperature=0.3,
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content.strip()
            return analysis
            
        except Exception as e:
            self.logger.error(f"AI估算分析也失败: {e}")
            return None
            
    def combine_analyses(self, analyses: Dict[str, str], current_date: str) -> str:
        """合并所有加密货币分析为单篇文章
        
        Args:
            analyses: 各币种分析结果字典
            current_date: 当前日期
            
        Returns:
            合并后的文章内容
        """
        # Hugo文章头部 (使用北京时间)
        beijing_tz = timezone(timedelta(hours=8))
        frontmatter = f"""---
title: "{current_date} 加密货币永续合约交易信号日报"
description: "专业分析BTC、ETH、BNB、SOL、BCH五大主流币种的永续合约交易机会，基于MCP市场周期理论提供精准入场信号"
date: {datetime.now(beijing_tz).isoformat()}
tags: ["加密货币", "永续合约", "交易信号", "技术分析", "BTC", "ETH", "BNB", "SOL", "BCH"]
categories: ["合约交易"]
author: "SmartWallex团队"
weight: 1
keywords: ["加密货币合约", "永续合约信号", "BTC分析", "ETH交易", "BNB策略", "SOL合约", "BCH信号", "技术分析", "交易策略"]
---

"""

        # 文章正文
        content = f"""# {current_date} 加密货币永续合约交易信号日报

> **声明**: 本报告基于技术分析提供参考信息，不构成投资建议。加密货币交易存在极高风险，请理性投资。

## 📊 市场概览

本日报基于Market Cycle Phases (MCP)分析框架，结合RSI、MACD、Bollinger Bands等核心技术指标，为五大主流加密货币提供专业的永续合约交易信号。

所有分析严格遵循风险管理原则：
- 风险回报比 ≥ 1:2
- 单笔交易风险不超过账户总资金2%
- 仅在MCP显示明确趋势时开仓

---

"""

        # 添加各币种分析
        for crypto in self.SUPPORTED_CRYPTOS:
            if crypto in analyses:
                content += f"## 💰 {crypto} 合约分析\n\n"
                content += f"{analyses[crypto]}\n\n"
                content += "---\n\n"
            else:
                content += f"## 💰 {crypto} 合约分析\n\n"
                content += f"⚠️ 暂时无法获取 {crypto} 的市场数据，建议暂时观望。\n\n"
                content += "---\n\n"
                
        # 文章结尾
        content += f"""## ⚠️ 风险提示

1. **高风险警告**: 永续合约交易具有极高风险，可能导致全部本金损失
2. **杠杆风险**: 建议新手使用1-3x杠杆，经验丰富者不超过5x
3. **市场波动**: 加密货币市场24小时交易，价格波动剧烈
4. **止损重要性**: 严格执行止损，控制单笔损失在账户总资金2%以内
5. **资金管理**: 永远不要投入超过承受能力的资金

## 📞 联系我们

- 🌐 官网: [SmartWallex.com](https://smartwallex.com)
- 📧 邮箱: contact@smartwallex.com  
- 🐦 Twitter: [@SmartWallex](https://twitter.com/SmartWallex)

*本报告由SmartWallex智能分析系统生成，基于公开市场数据和技术分析模型*
"""

        return frontmatter + content
        
    def save_article(self, content: str, current_date: str) -> str:
        """保存文章到指定目录
        
        Args:
            content: 文章内容
            current_date: 当前日期
            
        Returns:
            保存的文件路径
        """
        # 生成文件名 (使用北京时间)
        beijing_tz = timezone(timedelta(hours=8))
        timestamp = datetime.now(beijing_tz).strftime('%H%M%S')
        filename = f"crypto-swap-daily-{current_date}-{timestamp}.md"
        
        # 保存到content/posts目录
        posts_dir = script_dir.parent / 'content' / 'posts'
        posts_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = posts_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"文章已保存: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            raise
            
    def run_analysis(self) -> bool:
        """执行完整的分析流程 - 严格要求实时数据
        
        Returns:
            成功返回True，失败返回False
            
        Raises:
            RuntimeError: 当实时数据获取失败时抛出，上层调用者需要处理
        """
        try:
            # 使用北京时间 (UTC+8)
            beijing_tz = timezone(timedelta(hours=8))
            current_date = datetime.now(beijing_tz).strftime('%Y-%m-%d')
            self.logger.info(f"开始执行 {current_date} 加密货币合约分析")
            
            # 为每个币种生成分析
            analyses = {}
            failed_cryptos = []
            
            for crypto in self.SUPPORTED_CRYPTOS:
                try:
                    analysis = self.generate_analysis_for_crypto(crypto, current_date)
                    analyses[crypto] = analysis
                    self.logger.info(f"✅ {crypto} 分析生成成功")
                except RuntimeError as e:
                    # 实时数据失败，记录失败的币种
                    failed_cryptos.append(crypto)
                    self.logger.error(f"❌ {crypto} 分析生成失败: {e}")
                    continue
                except Exception as e:
                    # 其他错误，也记录为失败
                    failed_cryptos.append(crypto)
                    self.logger.error(f"❌ {crypto} 分析生成失败: {e}")
                    continue
            
            # 如果有任何币种失败，报错并暂停交易
            if failed_cryptos:
                error_msg = f"❌ CRITICAL: 以下币种实时数据获取失败，无法生成分析: {', '.join(failed_cryptos)}。为确保交易安全，程序已暂停。"
                self.logger.error(error_msg)
                
                # 通知用户交易暂停
                notify_trading_pause(error_msg, {
                    "failed_cryptos": failed_cryptos,
                    "total_cryptos": len(self.SUPPORTED_CRYPTOS),
                    "successful_cryptos": list(analyses.keys()),
                    "current_date": current_date,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                raise RuntimeError(error_msg)
            
            # 检查是否所有币种分析都成功
            if len(analyses) != len(self.SUPPORTED_CRYPTOS):
                missing_cryptos = set(self.SUPPORTED_CRYPTOS) - set(analyses.keys())
                error_msg = f"❌ CRITICAL: 部分币种分析生成失败: {', '.join(missing_cryptos)}。为确保数据完整性，程序已暂停。"
                self.logger.error(error_msg)
                
                notify_trading_pause(error_msg, {
                    "missing_cryptos": list(missing_cryptos),
                    "total_cryptos": len(self.SUPPORTED_CRYPTOS),
                    "successful_cryptos": list(analyses.keys()),
                    "current_date": current_date,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                raise RuntimeError(error_msg)
            
            # 所有币种分析成功，继续后续流程
            self.logger.info(f"✅ 所有 {len(analyses)} 个币种分析生成成功")
            
            # 合并分析并保存
            combined_content = self.combine_analyses(analyses, current_date)
            filepath = self.save_article(combined_content, current_date)
            
            self.logger.info(f"🎉 加密货币合约日报生成完成: {filepath}")
            self.logger.info(f"成功分析币种: {list(analyses.keys())}")
            return True
            
        except RuntimeError:
            # 重新抛出RuntimeError，让上层处理
            raise
        except Exception as e:
            error_msg = f"分析流程执行失败: {e}"
            self.logger.error(error_msg)
            
            # 通知用户
            notify_trading_pause(error_msg, {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            raise RuntimeError(error_msg)
        
        try:
            # 使用北京时间 (UTC+8)
            beijing_tz = timezone(timedelta(hours=8))
            current_date = datetime.now(beijing_tz).strftime('%Y-%m-%d')
            self.logger.info(f"开始执行 {current_date} 加密货币合约分析")
            
            # 为每个币种生成分析
            analyses = {}
            failed_cryptos = []
            
            for crypto in self.SUPPORTED_CRYPTOS:
                try:
                    analysis = self.generate_analysis_for_crypto(crypto, current_date)
                    analyses[crypto] = analysis
                    self.logger.info(f"✅ {crypto} 分析生成成功")
                except RuntimeError as e:
                    # 实时数据失败，记录失败的币种
                    failed_cryptos.append(crypto)
                    self.logger.error(f"❌ {crypto} 分析生成失败: {e}")
                    continue
                except Exception as e:
                    # 其他错误，也记录为失败
                    failed_cryptos.append(crypto)
                    self.logger.error(f"❌ {crypto} 分析生成失败: {e}")
                    continue
                    
            # 检查是否至少有一个分析成功
            if not analyses:
                self.logger.error("所有币种分析都失败了，终止流程")
                return False
                
            # 合并分析并保存
            combined_content = self.combine_analyses(analyses, current_date)
            filepath = self.save_article(combined_content, current_date)
            
            self.logger.info(f"加密货币合约日报生成完成: {filepath}")
            self.logger.info(f"成功分析币种: {list(analyses.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"分析流程执行失败: {e}")
            return False


def main():
    """主函数"""
    analyzer = CryptoSwapAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("✅ 加密货币合约日报生成成功")
        sys.exit(0)
    else:
        print("❌ 加密货币合约日报生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()