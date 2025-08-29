"""
文章翻译和总结模块
使用 GLM API 将英文文章翻译为中文并生成摘要
"""

import json
import time
import sys
import os
from typing import Dict, Tuple, Optional
from openai import OpenAI

# 添加父目录到路径以导入 glm_logger
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from glm_logger import GLMLogger, GLMClientWrapper
except ImportError:
    # 如果 glm_logger 不存在，创建简化版本
    print("Warning: glm_logger not found, using simplified version")
    
    class GLMLogger:
        def __init__(self):
            self.stats = {"total_calls": 0, "successful_calls": 0, "failed_calls": 0, 
                         "total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
        
        def get_daily_stats(self):
            return self.stats
    
    class GLMClientWrapper:
        def __init__(self, api_key, base_url, logger):
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.logger = logger
        
        def chat_completions_create(self, **kwargs):
            try:
                response = self.client.chat.completions.create(**kwargs)
                self.logger.stats["total_calls"] += 1
                self.logger.stats["successful_calls"] += 1
                if hasattr(response, 'usage') and response.usage:
                    self.logger.stats["total_tokens"] += response.usage.total_tokens
                    self.logger.stats["prompt_tokens"] += response.usage.prompt_tokens
                    self.logger.stats["completion_tokens"] += response.usage.completion_tokens
                return response
            except Exception as e:
                self.logger.stats["total_calls"] += 1
                self.logger.stats["failed_calls"] += 1
                raise e
from .config import (
    GLM_API_KEY, GLM_API_BASE, GLM_MODEL,
    TRANSLATION_TEMPERATURE, SUMMARY_TEMPERATURE,
    MAX_TOKENS_TRANSLATION, MAX_TOKENS_SUMMARY
)


class ChineseTranslator:
    """中文翻译和总结生成器"""
    
    def __init__(self, glm_api_key: str = None):
        self.api_key = glm_api_key or GLM_API_KEY
        self.client = None
        self.logger = None
        
        if self.api_key:
            try:
                # 初始化GLM日志记录器
                self.logger = GLMLogger()
                
                # 使用包装客户端，自动记录API调用
                self.client = GLMClientWrapper(
                    api_key=self.api_key,
                    base_url=GLM_API_BASE,
                    logger=self.logger
                )
                print("✅ GLM翻译客户端初始化成功")
            except Exception as e:
                print(f"❌ GLM客户端初始化失败: {e}")
                self.client = None
                self.logger = None
        else:
            print("❌ 缺少GLM API密钥，翻译功能将不可用")
    
    def translate_to_chinese(self, english_content: str, title: str = "") -> Optional[str]:
        """将英文内容翻译为中文"""
        if not self.client:
            print("❌ 翻译客户端未初始化")
            return None
        
        try:
            system_prompt = """你是一个专业的加密货币和区块链领域翻译专家。请将提供的英文文章翻译为自然流畅的中文，要求：

1. 保持专业术语的准确性（如DeFi、NFT、区块链等）
2. 翻译要符合中文表达习惯
3. 保留原文的结构和语调
4. 对于专业术语，首次出现时可以保留英文原文在括号中
5. 数字、时间、价格等信息保持原样
6. 保持段落结构

请直接输出翻译后的中文内容，不要添加任何解释或说明。"""

            user_prompt = f"""请翻译以下关于加密货币/区块链的英文文章：

标题：{title}

内容：
{english_content}"""

            print("🔄 正在翻译为中文...")
            
            completion = self.client.chat_completions_create(
                model=GLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TRANSLATION_TEMPERATURE,
                max_tokens=MAX_TOKENS_TRANSLATION
            )
            
            chinese_content = completion.choices[0].message.content.strip()
            print(f"✅ 翻译完成，长度: {len(chinese_content)} 字符")
            return chinese_content
            
        except Exception as e:
            print(f"❌ 翻译失败: {e}")
            return None
    
    def generate_summary(self, chinese_content: str, title: str = "") -> Optional[str]:
        """生成中文文章摘要"""
        if not self.client:
            print("❌ 摘要生成客户端未初始化")
            return None
        
        try:
            system_prompt = """你是一个专业的加密货币内容分析师。请为提供的中文文章生成一个精炼的摘要，要求：

1. 摘要长度控制在200-300字
2. 突出文章的核心要点和关键信息
3. 保持客观中性的语调
4. 包含重要的数据、事件或趋势
5. 适合作为文章的开头段落
6. 语言要专业且易懂

请直接输出摘要内容，不要添加"摘要："等标题。"""

            user_prompt = f"""请为以下中文文章生成摘要：

标题：{title}

文章内容：
{chinese_content}"""

            print("📝 正在生成文章摘要...")
            
            completion = self.client.chat_completions_create(
                model=GLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=SUMMARY_TEMPERATURE,
                max_tokens=MAX_TOKENS_SUMMARY
            )
            
            summary = completion.choices[0].message.content.strip()
            print(f"✅ 摘要生成完成，长度: {len(summary)} 字符")
            return summary
            
        except Exception as e:
            print(f"❌ 摘要生成失败: {e}")
            return None
    
    def translate_title(self, english_title: str) -> Optional[str]:
        """翻译文章标题"""
        if not self.client:
            print("❌ 标题翻译客户端未初始化")
            return None
        
        try:
            system_prompt = """你是一个专业的加密货币内容翻译专家。请将英文标题翻译为吸引人的中文标题，要求：

1. 保持原意准确
2. 符合中文表达习惯
3. 适合作为新闻或分析文章标题
4. 长度适中（20-50字）
5. 保留关键术语的专业性

请直接输出翻译后的中文标题。"""

            user_prompt = f"请翻译以下英文标题：{english_title}"

            print("🏷️ 正在翻译标题...")
            
            completion = self.client.chat_completions_create(
                model=GLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=TRANSLATION_TEMPERATURE,
                max_tokens=200
            )
            
            chinese_title = completion.choices[0].message.content.strip()
            # 清理可能的引号
            chinese_title = chinese_title.strip('"\'')
            print(f"✅ 标题翻译完成: {chinese_title}")
            return chinese_title
            
        except Exception as e:
            print(f"❌ 标题翻译失败: {e}")
            return None
    
    def process_article(self, article_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """处理完整文章：翻译标题、内容并生成摘要"""
        print(f"\n🔄 开始处理文章: {article_data.get('title', 'Untitled')[:50]}...")
        
        # 翻译标题
        chinese_title = self.translate_title(article_data['title'])
        if not chinese_title:
            print("❌ 标题翻译失败，跳过该文章")
            return None
        
        # 等待避免API限制
        time.sleep(1)
        
        # 翻译内容
        chinese_content = self.translate_to_chinese(
            article_data['content'], 
            article_data['title']
        )
        if not chinese_content:
            print("❌ 内容翻译失败，跳过该文章")
            return None
        
        # 等待避免API限制
        time.sleep(1)
        
        # 生成摘要
        summary = self.generate_summary(chinese_content, chinese_title)
        if not summary:
            print("❌ 摘要生成失败，使用默认摘要")
            summary = f"本文分析了{chinese_title}相关的链上数据和市场动态。"
        
        processed_article = {
            'original_title': article_data['title'],
            'chinese_title': chinese_title,
            'original_content': article_data['content'],
            'chinese_content': chinese_content,
            'summary': summary,
            'url': article_data.get('url', ''),
            'id': article_data.get('id', ''),
            'original_summary': article_data.get('summary', '')
        }
        
        print(f"✅ 文章处理完成: {chinese_title}")
        return processed_article
    
    def get_api_usage_stats(self) -> Dict[str, any]:
        """获取API使用统计"""
        if self.logger:
            return self.logger.get_daily_stats()
        return {"error": "日志记录器未初始化"}