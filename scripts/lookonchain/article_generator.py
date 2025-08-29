"""
Hugo 文章生成器模块
将翻译后的文章生成符合 Hugo 格式的 markdown 文件
"""

import os
import datetime
import json
import re
from typing import Dict, List, Optional, Set
from .config import (
    AUTHOR_INFO, DEFAULT_TAGS, DEFAULT_CATEGORIES, DEFAULT_KEYWORDS,
    DATA_DIR, LOOKONCHAIN_HISTORY_FILE
)


class ArticleGenerator:
    """Hugo 文章生成器"""
    
    def __init__(self):
        self.ensure_data_directory()
        self.history_file = LOOKONCHAIN_HISTORY_FILE
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def load_article_history(self) -> Set[str]:
        """加载已生成的文章历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('generated_articles', []))
            return set()
        except Exception as e:
            print(f"⚠️ 加载文章历史记录失败: {e}")
            return set()
    
    def save_article_history(self, article_ids: Set[str]):
        """保存已生成的文章历史记录"""
        try:
            data = {
                'last_updated': datetime.datetime.now().isoformat(),
                'total_articles': len(article_ids),
                'generated_articles': list(article_ids)
            }
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存 {len(article_ids)} 个文章记录")
        except Exception as e:
            print(f"⚠️ 保存文章历史记录失败: {e}")
    
    def is_article_generated(self, article_id: str, generated_articles: Set[str]) -> bool:
        """检查文章是否已经生成过"""
        return article_id in generated_articles
    
    def generate_filename(self, chinese_title: str, article_id: str) -> str:
        """生成文件名"""
        # 从中文标题生成安全的文件名
        filename_base = re.sub(r'[^\w\u4e00-\u9fa5\-]', '-', chinese_title)
        filename_base = re.sub(r'-+', '-', filename_base).strip('-')
        
        # 限制文件名长度
        if len(filename_base) > 50:
            filename_base = filename_base[:50]
        
        # 添加日期和ID确保唯一性
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filename = f"lookonchain-{filename_base}-{today}-{article_id[:8]}.md"
        
        return filename
    
    def generate_article_tags(self, chinese_content: str, chinese_title: str) -> List[str]:
        """基于内容生成相关标签"""
        tags = DEFAULT_TAGS.copy()
        
        # 关键词检测
        content_lower = (chinese_content + chinese_title).lower()
        
        keyword_mapping = {
            'defi': ['DeFi', '去中心化金融'],
            'nft': ['NFT', '数字收藏品'],
            'bitcoin': ['Bitcoin', 'BTC', '比特币'],
            'ethereum': ['Ethereum', 'ETH', '以太坊'],
            'whale': ['鲸鱼地址', '大户'],
            'exchange': ['交易所', '中心化交易'],
            'dao': ['DAO', '去中心化组织'],
            'token': ['代币分析', '代币经济学'],
            'mining': ['挖矿', '矿工'],
            'staking': ['质押', '权益证明']
        }
        
        for keyword, related_tags in keyword_mapping.items():
            if keyword in content_lower:
                tags.extend(related_tags)
        
        # 去重并限制数量
        return list(set(tags))[:8]
    
    def generate_hugo_frontmatter(self, article: Dict[str, str]) -> str:
        """生成Hugo前置matter"""
        
        now = datetime.datetime.now()
        date_str = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        
        # 处理标题中的特殊字符
        safe_title = article['chinese_title'].replace("'", "''").replace('"', '""')
        
        # 生成描述
        description = article['summary'][:150] + "..." if len(article['summary']) > 150 else article['summary']
        safe_description = description.replace("'", "''").replace('"', '""')
        
        # 生成标签
        tags = self.generate_article_tags(article['chinese_content'], article['chinese_title'])
        tags_str = str(tags).replace("'", '"')  # 使用双引号
        
        # 生成关键词
        keywords = DEFAULT_KEYWORDS.copy()
        keywords.append(f"{article['chinese_title']}分析")
        keywords_str = str(keywords).replace("'", '"')
        
        # 生成分类
        categories_str = str(DEFAULT_CATEGORIES).replace("'", '"')
        
        frontmatter = f"""+++
date = '{date_str}'
draft = false
title = '{safe_title}'
description = '{safe_description}'
summary = '{safe_description}'
tags = {tags_str}
categories = {categories_str}
keywords = {keywords_str}
author = '{AUTHOR_INFO["name"]}'
ShowToc = true
TocOpen = false
ShowReadingTime = true
ShowBreadCrumbs = true
ShowPostNavLinks = true
ShowWordCount = true
ShowShareButtons = true

[cover]
image = ""
alt = "LookOnChain链上数据分析"
caption = "深度解析区块链链上数据动态"
relative = false
hidden = false
+++"""
        
        return frontmatter
    
    def generate_article_content(self, article: Dict[str, str]) -> str:
        """生成完整的文章内容"""
        
        # 文章摘要部分
        content = f"""{{{{< alert >}}}}
**LookOnChain链上监控**: {article['summary']}
{{{{< /alert >}}}}

{article['chinese_content']}

## 📊 数据来源与分析

本文基于LookOnChain平台的链上数据分析生成。LookOnChain是业界领先的区块链数据分析平台，专注于追踪和分析链上资金流动、大户行为等关键信息。

### 🔗 相关链接
- **原文链接**: [{article.get('url', '#')}]({article.get('url', '#')})
- **LookOnChain平台**: [https://www.lookonchain.com/](https://www.lookonchain.com/)

### 📈 投资风险提示
以上内容仅为链上数据分析，不构成投资建议。加密货币投资存在高风险，价格波动剧烈，请理性投资并做好风险管理。投资前请充分了解项目基本面，不要投入超出承受能力的资金。

---

## 📞 关于作者

**{AUTHOR_INFO['name']}** - {AUTHOR_INFO['title']}

### 🔗 联系方式与平台

- **📧 邮箱**: [{AUTHOR_INFO['email']}](mailto:{AUTHOR_INFO['email']})
- **🐦 Twitter**: [{AUTHOR_INFO['twitter']}](https://twitter.com/{AUTHOR_INFO['twitter'].replace('@', '')})
- **💬 微信**: {AUTHOR_INFO['wechat']}
- **📱 Telegram**: [{AUTHOR_INFO['telegram']}]({AUTHOR_INFO['telegram']})
- **📢 Telegram频道**: [{AUTHOR_INFO['telegram_channel']}]({AUTHOR_INFO['telegram_channel']})
- **👥 加密情报TG群**: [{AUTHOR_INFO['telegram_group']}]({AUTHOR_INFO['telegram_group']})
- **🎥 YouTube频道**: [{AUTHOR_INFO['youtube']}]({AUTHOR_INFO['youtube']})

### 🌐 相关平台

- **📊 加密货币信息聚合网站**: [{AUTHOR_INFO['website']}]({AUTHOR_INFO['website']})
- **📖 公众号**: {AUTHOR_INFO['wechat_public']}

*欢迎关注我的各个平台，获取最新的加密货币市场分析和投资洞察！*"""
        
        return content
    
    def create_hugo_article(self, article: Dict[str, str], output_dir: str) -> Optional[str]:
        """创建完整的Hugo文章文件"""
        try:
            # 生成文件名
            filename = self.generate_filename(article['chinese_title'], article['id'])
            file_path = os.path.join(output_dir, filename)
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成前置matter
            frontmatter = self.generate_hugo_frontmatter(article)
            
            # 生成文章内容
            content = self.generate_article_content(article)
            
            # 组合完整文章
            full_article = f"{frontmatter}\n\n{content}\n"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_article)
            
            print(f"✅ 文章已生成: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 文章生成失败: {e}")
            return None
    
    def generate_daily_articles(self, processed_articles: List[Dict[str, str]]) -> Dict[str, any]:
        """生成当日的所有文章"""
        if not processed_articles:
            return {"success": False, "message": "没有文章需要生成", "generated": 0}
        
        print(f"📝 准备生成 {len(processed_articles)} 篇文章...")
        
        # 加载历史记录
        generated_articles = self.load_article_history()
        print(f"📚 已生成文章数量: {len(generated_articles)}")
        
        # 确定输出目录
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_dir = os.path.join(current_dir, 'content', 'posts')
        
        generated_count = 0
        generated_files = []
        newly_generated = set()
        
        for i, article in enumerate(processed_articles, 1):
            article_id = article['id']
            
            # 检查是否已生成
            if self.is_article_generated(article_id, generated_articles):
                print(f"⏭️ 跳过已生成文章 {i}: {article['chinese_title'][:30]}...")
                continue
            
            print(f"\n📄 生成文章 {i}: {article['chinese_title'][:50]}...")
            
            # 生成文章
            file_path = self.create_hugo_article(article, output_dir)
            if file_path:
                generated_count += 1
                generated_files.append(file_path)
                newly_generated.add(article_id)
                print(f"✅ 文章 {i} 生成成功")
            else:
                print(f"❌ 文章 {i} 生成失败")
        
        # 更新历史记录
        if newly_generated:
            all_generated = generated_articles.union(newly_generated)
            self.save_article_history(all_generated)
        
        result = {
            "success": generated_count > 0,
            "generated": generated_count,
            "total_processed": len(processed_articles),
            "files": generated_files,
            "newly_generated_ids": list(newly_generated)
        }
        
        if generated_count > 0:
            result["message"] = f"成功生成 {generated_count} 篇文章"
        else:
            result["message"] = "没有新文章生成（可能都已存在）"
        
        return result