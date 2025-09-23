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
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# 添加scripts目录到Python路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from openai_client import create_openai_client


class CryptoSwapAnalyzer:
    """加密货币合约分析器核心类"""
    
    # 支持的加密货币列表
    SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'BNB', 'SOL', 'BCH']
    
    def __init__(self):
        """初始化分析器"""
        self.setup_logging()
        self.openai_client = create_openai_client()
        self.expert_prompt = self._load_expert_prompt()
        
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
            
    def generate_analysis_for_crypto(self, crypto: str, current_date: str) -> Optional[str]:
        """为单个加密货币生成分析
        
        Args:
            crypto: 加密货币符号 (如 'BTC')
            current_date: 当前日期 (格式: 'YYYY-MM-DD')
            
        Returns:
            生成的分析内容，失败时返回None
        """
        try:
            # 构建针对特定代币的提示词
            crypto_prompt = self.expert_prompt.replace('HYPE', crypto)
            crypto_prompt = crypto_prompt.replace('2025-09-23', current_date)
            
            self.logger.info(f"开始为 {crypto} 生成合约分析...")
            
            response = self.openai_client.chat_completions_create(
                messages=[{
                    "role": "user", 
                    "content": crypto_prompt
                }],
                temperature=0.3,  # 降低随机性以确保专业性
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content.strip()
            self.logger.info(f"成功生成 {crypto} 分析，长度: {len(analysis)} 字符")
            return analysis
            
        except Exception as e:
            self.logger.error(f"生成 {crypto} 分析失败: {e}")
            return None
            
    def combine_analyses(self, analyses: Dict[str, str], current_date: str) -> str:
        """合并所有加密货币分析为单篇文章
        
        Args:
            analyses: 各币种分析结果字典
            current_date: 当前日期
            
        Returns:
            合并后的文章内容
        """
        # Hugo文章头部
        frontmatter = f"""---
title: "{current_date} 加密货币永续合约交易信号日报"
description: "专业分析BTC、ETH、BNB、SOL、BCH五大主流币种的永续合约交易机会，基于MCP市场周期理论提供精准入场信号"
date: {datetime.now(timezone.utc).isoformat()}
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
        # 生成文件名
        timestamp = datetime.now().strftime('%H%M%S')
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
        """执行完整的分析流程
        
        Returns:
            成功返回True，失败返回False
        """
        try:
            current_date = datetime.now().strftime('%Y-%m-%d')
            self.logger.info(f"开始执行 {current_date} 加密货币合约分析")
            
            # 为每个币种生成分析
            analyses = {}
            for crypto in self.SUPPORTED_CRYPTOS:
                analysis = self.generate_analysis_for_crypto(crypto, current_date)
                if analysis:
                    analyses[crypto] = analysis
                else:
                    self.logger.warning(f"{crypto} 分析生成失败，将在文章中标注")
                    
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