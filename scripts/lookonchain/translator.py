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

# 添加父目录到路径以导入统一客户端
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from openai_client import create_openai_client, extract_content_from_response, GLMLogger
from .config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
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
        # 首先检查是否是错误响应
        if hasattr(response, 'error') and response.error:
            print(f"❌ [{debug_context}] API返回错误: {response.error}")
            return None
            
        # 检查choices是否存在且有效
        if hasattr(response, 'choices') and response.choices:
            if not response.choices:
                print(f"⚠️ [{debug_context}] choices为空列表")
                return None
                
            choice = response.choices[0]
            
            # 检查message结构
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                content = choice.message.content
                if content and content.strip():
                    return content.strip()
                else:
                    print(f"⚠️ [{debug_context}] choices[0].message.content 为空")
                    
                    # 检查是否有其他字段
                    if hasattr(choice.message, 'role'):
                        print(f"🔍 [{debug_context}] message.role: {choice.message.role}")
                    if hasattr(choice, 'finish_reason'):
                        print(f"🔍 [{debug_context}] choice.finish_reason: {choice.finish_reason}")
                    if hasattr(choice, 'index'):
                        print(f"🔍 [{debug_context}] choice.index: {choice.index}")
        
        # 尝试检查完整的响应结构
        print(f"🔍 [{debug_context}] 完整响应分析:")
        if hasattr(response, '__dict__'):
            for key, value in response.__dict__.items():
                if key not in ['_client', '_request_id']:
                    print(f"    {key}: {type(value)} = {str(value)[:100] if len(str(value)) > 100 else value}")
        
        # 尝试其他可能的响应格式
        for attr_name in ['content', 'text', 'output', 'result']:
            if hasattr(response, attr_name):
                content = getattr(response, attr_name)
                if content and str(content).strip():
                    print(f"✅ [{debug_context}] 从 {attr_name} 字段找到内容")
                    return str(content).strip()
                else:
                    print(f"⚠️ [{debug_context}] response.{attr_name} 为空")
        
        # 如果是字典格式
        if isinstance(response, dict):
            for key in ['content', 'text', 'output', 'result', 'choices']:
                if key in response and response[key]:
                    content = str(response[key]).strip()
                    if content:
                        print(f"✅ [{debug_context}] 从字典 {key} 找到内容")
                        return content
        
        print(f"❌ [{debug_context}] 无法从任何字段提取内容")
        return None
        
    except Exception as e:
        print(f"❌ [{debug_context}] 解析响应时发生错误: {e}")
        import traceback
        print(f"🔍 [{debug_context}] 错误详情: {traceback.format_exc()}")
        return None


class ChineseTranslator:
    """中文翻译和总结生成器"""
    
    def __init__(self, openai_api_key: str = None):
        self.api_key = openai_api_key or OPENAI_API_KEY
        self.client = None
        self.logger = None
        
        # 检查API密钥是否有效
        if not self.api_key or self.api_key in ['your_openai_api_key_here', 'your_api_key_here', '']:
            print("❌ OpenAI API密钥未设置或使用示例密钥，翻译功能将不可用")
            print("📝 请在 .env.local 文件中设置有效的 OPENAI_API_KEY")
            return
        
        try:
            # 初始化日志记录器
            self.logger = GLMLogger()
            
            # 使用OpenAI兼容客户端
            self.client = create_openai_client(
                api_key=self.api_key,
                base_url=OPENAI_BASE_URL,
                model=OPENAI_MODEL,
                logger=self.logger
            )
            
            if self.client:
                print("✅ 翻译客户端初始化成功")
                # 测试API连接
                self._test_api_connection()
            else:
                print("❌ 翻译客户端创建失败")
                self.logger = None
            
        except Exception as e:
            print(f"❌ 翻译客户端初始化失败: {e}")
            self.client = None
            self.logger = None
    
    def _test_api_connection(self):
        """测试API连接是否正常"""
        try:
            print("🔧 测试API连接...")
            test_completion = self.client.chat_completions_create(
                messages=[{"role": "user", "content": "请回复'连接正常'"}],
                temperature=0.1,
                max_tokens=10
            )
            
            test_content = extract_content_from_response(test_completion, "API连接测试")
            if test_content:
                print(f"✅ API连接测试成功: {test_content}")
            else:
                print("⚠️ API连接测试失败：无法获取响应内容")
                
        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
            self.client = None  # 禁用客户端
    
    def translate_to_chinese(self, english_content: str, title: str = "") -> Optional[str]:
        """将英文内容翻译为中文"""
        if not self.client:
            print("❌ 翻译客户端未初始化")
            return None
        
        # 验证输入内容
        if not english_content or not english_content.strip():
            print("⚠️ 翻译内容为空")
            return None
        
        if len(english_content.strip()) < 50:
            print("⚠️ 翻译内容过短，跳过翻译")
            return english_content
        
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
            import traceback
            print(f"🔍 翻译错误详情: {traceback.format_exc()}")
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
    
    def _clean_fallback_content(self, raw_content: str) -> str:
        """
        清理用作fallback的原始内容，移除HTML、导航文本等无用信息
        """
        if not raw_content:
            return "未能获取有效文章内容"
        
        import re
        
        # 1. 移除HTML标签（如果存在）
        content = re.sub(r'<[^>]+>', ' ', raw_content)
        
        # 2. 移除常见的网站导航和UI文本
        navigation_patterns = [
            r'\b(Home|Login|Register|Logout|About|Contact|Menu|Navigation|Footer|Header|Search|Subscribe|Follow|Share|Like|Reply|Retweet|Tweet|Copy link|Download|Upload|Settings|Profile|Dashboard|Notifications)\b',
            r'\b(trending|popular|latest|hot|new|more|read more|continue reading|click here|learn more|show more|load more|view all|see all)\b',
            r'\b(APP|应用商店|登录|注册|配置文件|安全|注销|动态|文章|搜索历史|清除全部|趋势搜索|关注我们|加入|下载图片|复制链接|相关内容|原文|热点新闻|更多热门文章|更多)\b',
            r'Lookonchain\s*/\s*\d{4}\.\d{2}\.\d{2}',  # 移除Lookonchain日期格式
            r'X\s+关注Telegram\s+加入',  # 移除社交媒体关注文本
            r'\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}',  # 移除时间戳
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, ' ', content, flags=re.IGNORECASE)
        
        # 3. 移除重复的空白字符和换行
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # 4. 如果清理后内容过短，尝试提取主要段落
        if len(content) < 200:
            # 尝试提取包含关键词的段落
            sentences = content.split('。')
            relevant_sentences = []
            keywords = ['加密', '比特币', 'BTC', 'ETH', '以太坊', '交易', '投资', '区块链', '智能', '资金', '地址', '转账', '美元', '$', 'USDT', 'DeFi', '代币']
            
            for sentence in sentences:
                if any(keyword in sentence for keyword in keywords) and len(sentence) > 20:
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                content = '。'.join(relevant_sentences[:3]) + '。'
        
        # 5. 确保最小长度
        if len(content) < 100:
            content = f"文章主要内容：{content[:500]}..." if len(content) > 500 else content
            if not content.strip():
                content = "由于技术原因，暂时无法获取完整的文章内容。请访问原文链接查看详细信息。"
        
        return content
    
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
            print("⚠️ 内容翻译失败，使用清理后的原始内容")
            original_content = article_data.get('content', '未能获取文章内容')
            # 清理原始内容中的HTML和导航文本
            chinese_content = self._clean_fallback_content(original_content)
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