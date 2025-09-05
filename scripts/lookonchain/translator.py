"""
文章翻译和总结模块
使用 GLM API 将英文文章翻译为中文并生成摘要
"""

import json
import time
import sys
import os
from typing import Dict, Tuple, Optional, Any
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


def extract_content_from_response(response: Any, debug_context: str = "") -> Optional[str]:
    """
    稳健地从GLM API响应中提取文本内容
    支持多种可能的响应格式，并提供详细的调试信息
    """
    if not response:
        print(f"⚠️ [{debug_context}] 响应为空")
        return None
    
    try:
        # 尝试标准OpenAI格式：response.choices[0].message.content
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                content = choice.message.content
                if content and content.strip():
                    return content.strip()
                else:
                    print(f"⚠️ [{debug_context}] choices[0].message.content 为空")
        
        # 尝试直接的content字段
        if hasattr(response, 'content'):
            content = response.content
            if content and content.strip():
                return content.strip()
            else:
                print(f"⚠️ [{debug_context}] response.content 为空")
        
        # 尝试text字段
        if hasattr(response, 'text'):
            text = response.text
            if text and text.strip():
                return text.strip()
            else:
                print(f"⚠️ [{debug_context}] response.text 为空")
        
        # 尝试字典格式
        if isinstance(response, dict):
            for key in ['content', 'text', 'output', 'result']:
                if key in response and response[key]:
                    content = str(response[key]).strip()
                    if content:
                        return content
                    else:
                        print(f"⚠️ [{debug_context}] response['{key}'] 为空")
        
        # 如果所有标准格式都失败，记录完整响应结构用于调试
        print(f"🔍 [{debug_context}] 无法解析响应，响应结构:")
        if hasattr(response, '__dict__'):
            print(f"    属性: {list(response.__dict__.keys())}")
        elif isinstance(response, dict):
            print(f"    字典键: {list(response.keys())}")
        else:
            print(f"    类型: {type(response)}")
            print(f"    内容: {str(response)[:200]}...")
        
        return None
        
    except Exception as e:
        print(f"❌ [{debug_context}] 解析响应时发生错误: {e}")
        return None


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
            
            chinese_content = extract_content_from_response(completion, "内容翻译")
            if chinese_content:
                print(f"✅ 翻译完成，长度: {len(chinese_content)} 字符")
                return chinese_content
            else:
                print("❌ 无法从响应中提取翻译内容")
                return None
            
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
            
            summary = extract_content_from_response(completion, "摘要生成")
            if summary:
                print(f"✅ 摘要生成完成，长度: {len(summary)} 字符")
                return summary
            else:
                print("❌ 无法从响应中提取摘要内容")
                return None
            
        except Exception as e:
            print(f"❌ 摘要生成失败: {e}")
            return None
    
    def translate_title(self, english_title: str, max_retries: int = 2) -> str:
        """
        翻译文章标题（带重试机制和fallback）
        返回翻译后的标题，如果翻译失败则返回原标题
        """
        if not english_title or not english_title.strip():
            return "LookOnChain 链上数据分析"
        
        original_title = english_title.strip()
        
        if not self.client:
            print("⚠️ 标题翻译客户端未初始化，使用原标题")
            return original_title
        
        system_prompt = """你是一个专业的加密货币内容翻译专家。请将英文标题翻译为吸引人的中文标题，要求：

1. 保持原意准确
2. 符合中文表达习惯
3. 适合作为新闻或分析文章标题
4. 长度适中（20-50字）
5. 保留关键术语的专业性

请直接输出翻译后的中文标题。"""

        user_prompt = f"请翻译以下英文标题：{original_title}"

        for attempt in range(max_retries + 1):
            try:
                print(f"🏷️ 正在翻译标题... (尝试 {attempt + 1}/{max_retries + 1})")
                
                completion = self.client.chat_completions_create(
                    model=GLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=TRANSLATION_TEMPERATURE,
                    max_tokens=200
                )
                
                # 使用稳健的内容提取函数
                chinese_title = extract_content_from_response(
                    completion, 
                    f"标题翻译-尝试{attempt + 1}"
                )
                
                if chinese_title:
                    # 清理可能的引号和多余空格
                    chinese_title = chinese_title.strip().strip('"\'').strip()
                    
                    if chinese_title:  # 确保清理后不为空
                        print(f"✅ 标题翻译完成: {chinese_title}")
                        return chinese_title
                
                # 如果这次尝试失败，等待后重试
                if attempt < max_retries:
                    print(f"⚠️ 第 {attempt + 1} 次翻译无效，等待后重试...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ 第 {attempt + 1} 次标题翻译出错: {e}")
                if attempt < max_retries:
                    print(f"⏳ 等待 2 秒后重试...")
                    time.sleep(2)
        
        # 所有尝试都失败，使用原标题作为fallback
        print(f"⚠️ 标题翻译全部失败，使用原标题: {original_title}")
        return original_title
    
    def process_article(self, article_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        处理完整文章：翻译标题、内容并生成摘要
        即使某些步骤失败，也尽可能生成可用的文章
        """
        original_title = article_data.get('title', 'Untitled')
        print(f"\n🔄 开始处理文章: {original_title[:50]}...")
        
        # 记录处理结果
        processing_stats = {
            'title_translation': False,
            'content_translation': False,
            'summary_generation': False
        }
        
        # 第1步：翻译标题（现在永远有fallback，不会失败）
        print("📋 步骤1: 翻译标题")
        chinese_title = self.translate_title(original_title)
        processing_stats['title_translation'] = (chinese_title != original_title)
        
        # 等待避免API限制
        time.sleep(1)
        
        # 第2步：翻译内容
        print("📄 步骤2: 翻译内容")
        chinese_content = self.translate_to_chinese(
            article_data.get('content', ''), 
            original_title
        )
        
        if not chinese_content:
            print("⚠️ 内容翻译失败，使用原始内容")
            chinese_content = article_data.get('content', '未能获取文章内容')
        else:
            processing_stats['content_translation'] = True
        
        # 等待避免API限制
        time.sleep(1)
        
        # 第3步：生成摘要（有多重fallback策略）
        print("📝 步骤3: 生成摘要")
        summary = self.generate_summary(chinese_content, chinese_title)
        
        if not summary:
            print("⚠️ 摘要生成失败，使用fallback策略")
            # 尝试使用原始摘要
            original_summary = article_data.get('summary', '').strip()
            if original_summary:
                print("📋 使用原始英文摘要作为fallback")
                summary = original_summary
            else:
                # 生成基础摘要
                print("🔧 生成基础摘要")
                summary = f"本文分析了{chinese_title}相关的链上数据和市场动态，提供了重要的市场洞察。"
        else:
            processing_stats['summary_generation'] = True
        
        # 构建最终文章数据
        processed_article = {
            'original_title': original_title,
            'chinese_title': chinese_title,
            'original_content': article_data.get('content', ''),
            'chinese_content': chinese_content,
            'summary': summary,
            'url': article_data.get('url', ''),
            'id': article_data.get('id', ''),
            'original_summary': article_data.get('summary', ''),
            'processing_stats': processing_stats
        }
        
        # 输出处理结果统计
        successful_steps = sum(processing_stats.values())
        total_steps = len(processing_stats)
        
        if successful_steps == total_steps:
            print(f"✅ 文章完全处理成功: {chinese_title}")
        elif successful_steps > 0:
            print(f"⚠️ 文章部分处理成功 ({successful_steps}/{total_steps}): {chinese_title}")
        else:
            print(f"⚠️ 文章基本处理完成（使用fallback内容）: {chinese_title}")
        
        return processed_article
    
    def get_api_usage_stats(self) -> Dict[str, any]:
        """获取API使用统计"""
        if self.logger:
            return self.logger.get_daily_stats()
        return {"error": "日志记录器未初始化"}