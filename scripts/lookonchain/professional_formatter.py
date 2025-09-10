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
        return f"""你是一个专业的加密货币和区块链内容编辑专家。你的任务是将LookOnChain的链上数据分析内容，重新组织和扩展为一篇完整的分析文章。

**重要提醒**：你处理的是LookOnChain的实时链上数据分析内容，不是平台评测。请基于原始内容进行专业化的扩展和组织，不要套用其他平台的评测模板。

**文章结构要求**：

## 📊 核心分析内容
- 基于原始数据的专业解读
- 关键数据点和趋势分析
- 市场洞察和投资信号

## 🔍 深度技术分析
- 链上数据的技术层面分析
- 交易模式和行为分析
- 潜在影响和风险评估

## 📈 市场影响与展望
- 对相关项目的影响分析
- 市场趋势和机会识别
- 专业投资建议和风险提示

## 🎯 总结与建议
- 核心观点总结
- 投资决策参考
- 后续关注重点

**写作要求**：
1. 保持专业的分析语调，基于原始数据进行扩展
2. 增加背景信息和技术解释，提升内容深度
3. 确保数据的准确性和分析的专业性
4. 添加相关的市场背景和投资建议
5. 保持内容的连贯性和可读性
6. 输出完整的markdown内容（不包含frontmatter）

请直接输出格式化后的markdown内容，不要添加任何解释。"""
    
    def _build_user_prompt(self, article_data: Dict[str, str]) -> str:
        """构建用户提示词"""
        return f"""请将以下LookOnChain链上数据分析内容，重新组织为一篇专业的分析文章：

原始标题：{article_data.get('original_title', '')}
中文标题：{article_data.get('chinese_title', '')}

文章摘要：
{article_data.get('summary', '')}

中文翻译内容：
{article_data.get('chinese_content', '')}

请基于以上LookOnChain的链上数据内容，生成一篇专业的分析文章。要求：
1. 保持原始数据的准确性
2. 增加专业的技术分析和市场洞察
3. 提供投资建议和风险评估
4. 按照要求的结构组织内容
5. 保持分析的专业性和客观性"""
    
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