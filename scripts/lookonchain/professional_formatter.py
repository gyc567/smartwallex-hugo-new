"""
专业格式化内容生成器
基于大模型，将翻译后的内容格式化为符合md-template.md规范的专业评测文章
"""

import os
import sys
import re
from typing import Dict, Optional, Any

# 添加父目录到路径以导入统一客户端
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from openai_client import create_openai_client, extract_content_from_response

from .config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    PROFESSIONAL_FORMAT_TEMPERATURE, MAX_TOKENS_PROFESSIONAL_FORMAT
)


class ProfessionalFormatter:
    """专业格式化内容生成器"""
    
    def __init__(self, openai_api_key: str = None, logger=None):
        self.api_key = openai_api_key or OPENAI_API_KEY
        self.client = None
        self.logger = logger
        self.template_content = self._load_template()
        
        # 检查API密钥是否有效
        if not self.api_key or self.api_key in ['your_openai_api_key_here', 'your_api_key_here', '']:
            print("❌ OpenAI API密钥未设置，专业格式化功能将不可用")
            return
        
        try:
            # 使用OpenAI兼容客户端
            self.client = create_openai_client(
                api_key=self.api_key,
                base_url=OPENAI_BASE_URL,
                model=OPENAI_MODEL,
                logger=self.logger
            )
            
            if self.client:
                print("✅ 专业格式化客户端初始化成功")
            else:
                print("❌ 专业格式化客户端创建失败")
                
        except Exception as e:
            print(f"❌ 专业格式化客户端初始化失败: {e}")
            self.client = None
    
    def _load_template(self) -> str:
        """加载md-template.md模板内容"""
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_path = os.path.join(current_dir, 'md-template.md')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ 无法加载模板文件: {e}")
            return ""
    
    def format_content(self, article_data: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        将翻译后的内容格式化为专业评测文章
        
        Args:
            article_data: 包含翻译后内容的文章数据
            
        Returns:
            格式化后的文章数据，包含专业内容结构
        """
        if not self.client:
            print("❌ 专业格式化客户端未初始化，跳过格式化")
            return article_data
        
        if not self.template_content:
            print("⚠️ 模板内容为空，跳过格式化")
            return article_data
        
        try:
            print("🎨 开始专业格式化处理...")
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt()
            
            # 构建用户提示词
            user_prompt = self._build_user_prompt(article_data)
            
            # 调用大模型进行格式化
            completion = self.client.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=PROFESSIONAL_FORMAT_TEMPERATURE,
                max_tokens=MAX_TOKENS_PROFESSIONAL_FORMAT
            )
            
            formatted_content = extract_content_from_response(completion, "专业格式化")
            
            if formatted_content:
                print(f"✅ 专业格式化完成，长度: {len(formatted_content)} 字符")
                
                # 更新文章数据
                updated_article = article_data.copy()
                updated_article['formatted_content'] = formatted_content
                updated_article['is_professionally_formatted'] = True
                
                return updated_article
            else:
                print("❌ 专业格式化失败，使用原始内容")
                return article_data
                
        except Exception as e:
            print(f"❌ 专业格式化过程出错: {e}")
            return article_data
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""你是一个专业的加密货币和区块链内容编辑专家。你的任务是将LookOnChain的链上数据分析内容，按照提供的专业模板格式，重新组织和扩展为一篇完整的专业评测文章。

模板格式规范：
{self.template_content[:2000]}...

要求：
1. 严格按照模板的markdown格式和结构
2. 保持专业、客观的评测语调
3. 将原始内容扩展为完整的评测文章，包含：
   - 平台概览与核心价值
   - 核心功能深度评测
   - 完整使用指南
   - 订阅计划与性价比分析
   - 优缺点全面分析
   - 竞品对比分析
   - 使用建议与最佳实践
   - 总结评价和评分表格
4. 保留原始的技术数据和关键信息
5. 确保内容连贯性和专业性
6. 输出完整的markdown内容（不包含frontmatter）

请直接输出格式化后的markdown内容，不要添加任何解释。"""
    
    def _build_user_prompt(self, article_data: Dict[str, str]) -> str:
        """构建用户提示词"""
        return f"""请将以下LookOnChain链上数据分析内容，按照专业模板格式重新组织为完整的评测文章：

原始标题：{article_data.get('original_title', '')}
中文标题：{article_data.get('chinese_title', '')}

原始内容：
{article_data.get('original_content', '')}

中文翻译内容：
{article_data.get('chinese_content', '')}

文章摘要：
{article_data.get('summary', '')}

请基于以上内容，生成一篇符合模板格式的专业评测文章。保持原始数据和关键信息的准确性，同时按照模板结构进行专业化的内容组织和扩展。"""
    
    def extract_formatted_sections(self, formatted_content: str) -> Dict[str, str]:
        """
        从格式化内容中提取各个章节
        用于更细粒度的内容控制
        """
        sections = {}
        
        # 定义章节模式
        section_patterns = {
            'overview': r'## 🎯 平台概览与核心价值(.*?)(?=##|$)',
            'features': r'## 🛠️ 核心功能深度评测(.*?)(?=##|$)',
            'guide': r'## 📚 完整使用指南(.*?)(?=##|$)',
            'pricing': r'## 💰 订阅计划与性价比分析(.*?)(?=##|$)',
            'analysis': r'## ⚖️ 优缺点全面分析(.*?)(?=##|$)',
            'comparison': r'## 🏆 竞品对比分析(.*?)(?=##|$)',
            'recommendations': r'## 🎯 使用建议与最佳实践(.*?)(?=##|$)',
            'summary': r'## 📊 总结评价(.*?)(?=##|$)'
        }
        
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, formatted_content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(1).strip()
            else:
                sections[section_name] = ""
        
        return sections