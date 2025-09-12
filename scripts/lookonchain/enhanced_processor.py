#!/usr/bin/env python3
"""
LookOnChain 增强文章处理模块
集成了翻译、AI摘要生成和内容去重功能
"""

import json
import time
from typing import Dict, List, Optional
from .config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    TRANSLATION_TEMPERATURE, MAX_TOKENS_TRANSLATION,
    SUMMARY_TEMPERATURE, MAX_TOKENS_SUMMARY
)
from .history_manager import ArticleHistoryManager
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from openai_client import OpenAIClientWrapper


class EnhancedArticleProcessor:
    """增强的文章处理器"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        
        # 初始化OpenAI客户端
        self.client = OpenAIClientWrapper(
            api_key=self.openai_api_key,
            base_url=OPENAI_BASE_URL,
            model=OPENAI_MODEL
        )
        
        # 初始化历史管理器
        self.history_manager = ArticleHistoryManager()
        
        # API调用统计
        self.api_calls = {
            'translation': 0,
            'summary': 0,
            'failed': 0
        }
        
        print("🚀 增强文章处理器初始化完成")
    
    def translate_article(self, title: str, content: str) -> Dict[str, str]:
        """翻译文章为中文"""
        try:
            print("🔄 开始翻译文章...")
            print(f"📝 原文标题: {title[:50]}...")
            
            # 构建翻译提示
            translation_prompt = f"""
请将以下LookOnChain文章翻译为中文。要求：
1. 保持专业术语的准确性
2. 保持原文的技术性和专业性
3. 确保翻译后的中文流畅自然
4. 保留数据和技术细节
5. 适当调整表达方式以符合中文阅读习惯

标题：{title}

内容：
{content}

请以JSON格式返回翻译结果，包含"title"和"content"字段。
"""
            
            response = self.client.chat_completions_create(
                messages=[
                    {"role": "system", "content": "你是一位专业的区块链技术翻译专家，精通加密货币和区块链领域的术语翻译。"},
                    {"role": "user", "content": translation_prompt}
                ],
                temperature=TRANSLATION_TEMPERATURE,
                max_tokens=MAX_TOKENS_TRANSLATION
            )
            
            if response and hasattr(response, 'choices') and response.choices:
                content_text = response.choices[0].message.content
                print(f"🔤 API返回内容长度: {len(content_text)} 字符")
                
                # 尝试解析JSON响应
                try:
                    translation_result = json.loads(content_text)
                    translated_title = translation_result.get('title', title)
                    translated_content = translation_result.get('content', content)
                    
                    # 验证翻译结果
                    if translated_title == title and translated_content == content:
                        print("⚠️ 警告：翻译内容与原文相同，可能翻译失败")
                    
                    self.api_calls['translation'] += 1
                    print("✅ 文章翻译完成")
                    print(f"📝 译文标题: {translated_title[:50]}...")
                    
                    return {
                        'title': translated_title,
                        'content': translated_content,
                        'success': True
                    }
                    
                except json.JSONDecodeError as e:
                    # 如果JSON解析失败，使用原始响应
                    self.api_calls['translation'] += 1
                    print(f"⚠️ 翻译完成，但JSON解析失败: {e}")
                    print(f"🔤 原始响应: {content_text[:200]}...")
                    
                    # 尝试从文本中提取翻译
                    if any(char in content_text for char in ['的', '了', '是', '在', '有', '和', '与', '中']):
                        return {
                            'title': title,
                            'content': content_text,
                            'success': True
                        }
                    else:
                        return {
                            'title': title,
                            'content': content,
                            'success': False
                        }
            else:
                self.api_calls['failed'] += 1
                print("❌ 翻译失败：API响应无效")
                return {'title': title, 'content': content, 'success': False}
                
        except Exception as e:
            self.api_calls['failed'] += 1
            print(f"❌ 翻译失败：{e}")
            return {'title': title, 'content': content, 'success': False}
    
    def generate_ai_summary(self, title: str, content: str) -> str:
        """生成AI摘要"""
        try:
            print("🤖 开始生成AI摘要...")
            
            # 构建摘要提示
            summary_prompt = f"""
请为以下LookOnChain文章生成一个专业的中文AI摘要。要求：
1. 提炼文章的核心观点和关键信息
2. 包含重要的数据、地址和事件
3. 分析文章的洞察和意义
4. 字数控制在300-500字
5. 保持专业性和可读性

标题：{title}

内容：
{content}

请直接返回摘要内容，不需要其他格式。
"""
            
            response = self.client.chat_completions_create(
                messages=[
                    {"role": "system", "content": "你是一位区块链分析专家，擅长提炼和分析链上数据洞察。"},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=SUMMARY_TEMPERATURE,
                max_tokens=MAX_TOKENS_SUMMARY
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                summary = response['choices'][0]['message']['content'].strip()
                
                self.api_calls['summary'] += 1
                print("✅ AI摘要生成完成")
                
                return summary
            else:
                self.api_calls['failed'] += 1
                print("❌ AI摘要生成失败：API响应无效")
                return ""
                
        except Exception as e:
            self.api_calls['failed'] += 1
            print(f"❌ AI摘要生成失败：{e}")
            return ""
    
    def process_article(self, article: Dict) -> Optional[Dict]:
        """处理单篇文章：翻译 + AI摘要 + 去重检查"""
        title = article.get('title', '')
        content = article.get('content', '')
        url = article.get('url', '')
        
        if not title or not content:
            print(f"⚠️ 文章信息不完整，跳过处理")
            return None
        
        # 检查是否重复
        if self.history_manager.is_duplicate(article):
            print(f"🔍 发现重复文章，跳过处理：{title[:50]}...")
            return None
        
        print(f"\n📝 开始处理文章：{title[:60]}...")
        
        # 步骤1：翻译文章
        translation_result = self.translate_article(title, content)
        translated_title = translation_result['title']
        translated_content = translation_result['content']
        translation_success = translation_result['success']
        
        # 步骤2：生成AI摘要
        ai_summary = ""
        if translation_success:
            ai_summary = self.generate_ai_summary(translated_title, translated_content)
        
        # 构建处理后的文章数据
        processed_article = {
            'title': translated_title,
            'content': translated_content,  # 翻译后的内容作为主内容
            'translated_content': translated_content,  # 明确的翻译内容字段
            'summary': ai_summary,
            'url': url,
            'original_title': title,
            'original_content': content,
            'translation_success': translation_success,
            'has_summary': bool(ai_summary),
            'processed_at': time.time(),
            'api_calls': self.api_calls.copy()
        }
        
        # 添加到历史记录
        self.history_manager.add_article(article)
        
        print(f"✅ 文章处理完成：{translated_title[:50]}...")
        return processed_article
    
    def process_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """批量处理文章"""
        print(f"🚀 开始批量处理 {len(articles)} 篇文章...")
        
        processed_articles = []
        failed_count = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\n📰 处理文章 {i}/{len(articles)}")
            
            try:
                processed_article = self.process_article(article)
                if processed_article:
                    processed_articles.append(processed_article)
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ 处理文章 {i} 时发生错误：{e}")
        
        # 打印处理结果
        success_count = len(processed_articles)
        print(f"\n📊 批量处理完成:")
        print(f"✅ 成功处理: {success_count} 篇")
        print(f"❌ 处理失败: {failed_count} 篇")
        print(f"📝 总有效率: {success_count/len(articles)*100:.1f}%")
        
        # 打印API使用统计
        print(f"\n🤖 API使用统计:")
        print(f"🔤 翻译调用: {self.api_calls['translation']} 次")
        print(f"📝 摘要调用: {self.api_calls['summary']} 次")
        print(f"❌ 失败调用: {self.api_calls['failed']} 次")
        
        return processed_articles
    
    def get_api_statistics(self) -> Dict:
        """获取API使用统计"""
        return {
            'translation_calls': self.api_calls['translation'],
            'summary_calls': self.api_calls['summary'],
            'failed_calls': self.api_calls['failed'],
            'total_calls': sum(self.api_calls.values()),
            'success_rate': (self.api_calls['translation'] + self.api_calls['summary']) / max(sum(self.api_calls.values()), 1)
        }
    
    def print_history_statistics(self):
        """打印历史统计信息"""
        self.history_manager.print_statistics()