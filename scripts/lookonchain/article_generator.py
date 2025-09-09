"""
Hugo 文章生成器模块
将翻译后的文章生成符合 Hugo 格式的 markdown 文件
"""

import os
import datetime
import json
import re
import hashlib
from typing import Dict, List, Optional, Set
from .config import (
    AUTHOR_INFO, DEFAULT_TAGS, DEFAULT_CATEGORIES, DEFAULT_KEYWORDS,
    DATA_DIR, LOOKONCHAIN_HISTORY_FILE
)
from .professional_formatter import ProfessionalFormatter


class ArticleGenerator:
    """Hugo 文章生成器"""
    
    def __init__(self, openai_api_key: str = None, logger=None):
        self.ensure_data_directory()
        self.history_file = LOOKONCHAIN_HISTORY_FILE
        self.content_history_file = os.path.join(DATA_DIR, 'content_hashes.json')
        # 初始化专业格式化器
        self.formatter = ProfessionalFormatter(openai_api_key, logger)
        print("✅ ArticleGenerator初始化完成")
    
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
    
    def load_content_history(self) -> Dict[str, Dict]:
        """加载内容哈希历史记录，用于检测重复内容"""
        try:
            if os.path.exists(self.content_history_file):
                with open(self.content_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('content_hashes', {})
            return {}
        except Exception as e:
            print(f"⚠️ 加载内容历史记录失败: {e}")
            return {}
    
    def save_content_history(self, content_history: Dict[str, Dict]):
        """保存内容哈希历史记录"""
        try:
            data = {
                'last_updated': datetime.datetime.now().isoformat(),
                'total_hashes': len(content_history),
                'content_hashes': content_history
            }
            with open(self.content_history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存 {len(content_history)} 个内容哈希记录")
        except Exception as e:
            print(f"⚠️ 保存内容历史记录失败: {e}")
    
    def generate_content_hash(self, content: str, title: str) -> str:
        """生成内容哈希，用于检测重复内容"""
        # 组合标题和内容生成哈希
        combined_text = f"{title}{content}"
        return hashlib.md5(combined_text.encode('utf-8')).hexdigest()
    
    def generate_semantic_hash(self, content: str) -> str:
        """生成语义哈希，用于检测相似内容"""
        # 提取关键词和关键信息
        import re
        
        # 提取数字（金额、数量等）
        numbers = re.findall(r'\$[\d,]+|\d+\s*(USD|美元|百万|亿|万|BTC|ETH)', content)
        numbers = sorted(set(numbers))  # 去重排序
        
        # 提取加密货币关键词
        crypto_terms = ['比特币', 'BTC', '以太坊', 'ETH', 'DeFi', 'NFT', '代币', '交易所', '钱包', '地址']
        found_terms = [term for term in crypto_terms if term in content]
        
        # 提取时间信息
        dates = re.findall(r'\d{4}\.\d{2}\.\d{2}|\d{1,2}\s*月|\d{1,2}\s*日', content)
        dates = sorted(set(dates))
        
        # 组合关键信息生成语义哈希
        semantic_content = f"{'|'.join(found_terms)}|{'|'.join(numbers)}|{'|'.join(dates)}"
        return hashlib.md5(semantic_content.encode('utf-8')).hexdigest()
    
    def is_duplicate_content(self, article: Dict[str, str], url_history: Set[str], content_history: Dict[str, Dict]) -> Dict[str, bool]:
        """检查是否为重复内容"""
        article_id = article['id']
        title = article.get('chinese_title', article.get('original_title', ''))
        content = article.get('chinese_content', article.get('original_content', ''))
        
        duplicate_info = {
            'url_duplicate': False,
            'content_duplicate': False,
            'semantic_duplicate': False,
            'is_duplicate': False
        }
        
        # 1. 检查URL重复
        if article_id in url_history:
            duplicate_info['url_duplicate'] = True
            print(f"⚠️ 检测到URL重复: {title[:30]}...")
        
        # 2. 检查内容哈希重复
        content_hash = self.generate_content_hash(content, title)
        if content_hash in content_history:
            duplicate_info['content_duplicate'] = True
            existing_record = content_history[content_hash]
            print(f"⚠️ 检测到内容重复: {title[:30]}... (与 {existing_record.get('title', 'unknown')} 重复)")
        
        # 3. 检查语义重复
        semantic_hash = self.generate_semantic_hash(content)
        if semantic_hash in content_history:
            existing_record = content_history[semantic_hash]
            # 检查时间间隔，避免误判时效性内容
            existing_date = existing_record.get('date', '')
            if existing_date:
                try:
                    from datetime import datetime as dt
                    existing_dt = dt.fromisoformat(existing_date.replace('Z', '+00:00'))
                    current_dt = datetime.datetime.now()
                    days_diff = (current_dt - existing_dt).days
                    
                    # 如果超过7天，认为是不同的内容
                    if days_diff <= 7:
                        duplicate_info['semantic_duplicate'] = True
                        print(f"⚠️ 检测到语义重复: {title[:30]}... (与 {existing_record.get('title', 'unknown')} 相似，间隔 {days_diff} 天)")
                except:
                    # 如果日期解析失败，保守判断为重复
                    duplicate_info['semantic_duplicate'] = True
                    print(f"⚠️ 检测到语义重复: {title[:30]}... (与 {existing_record.get('title', 'unknown')} 相似)")
        
        # 综合判断是否为重复
        duplicate_info['is_duplicate'] = (
            duplicate_info['url_duplicate'] or 
            duplicate_info['content_duplicate'] or 
            duplicate_info['semantic_duplicate']
        )
        
        return duplicate_info
    
    def add_to_content_history(self, article: Dict[str, str], content_history: Dict[str, Dict]):
        """添加到内容历史记录"""
        title = article.get('chinese_title', article.get('original_title', ''))
        content = article.get('chinese_content', article.get('original_content', ''))
        article_id = article['id']
        
        # 生成哈希
        content_hash = self.generate_content_hash(content, title)
        semantic_hash = self.generate_semantic_hash(content)
        
        # 记录信息
        record = {
            'id': article_id,
            'title': title,
            'url': article.get('url', ''),
            'date': datetime.datetime.now().isoformat(),
            'content_hash': content_hash,
            'semantic_hash': semantic_hash
        }
        
        # 保存两种哈希
        content_history[content_hash] = record
        content_history[semantic_hash] = record
        
        print(f"📝 已添加到内容历史: {title[:30]}...")
    
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
    
    def generate_english_slug(self, chinese_title: str, date_obj: datetime.datetime) -> str:
        """基于中文标题生成英文slug"""
        date_str = date_obj.strftime('%Y-%m-%d')
        
        # 常见加密货币术语映射
        crypto_terms = {
            '比特币': 'bitcoin',
            'BTC': 'btc', 
            '以太坊': 'ethereum',
            'ETH': 'eth',
            '鲸鱼': 'whale',
            '地址': 'address',
            '交易': 'transaction',
            '资金': 'fund',
            '转账': 'transfer',
            '流入': 'inflow',
            '流出': 'outflow',
            '交易所': 'exchange',
            '币安': 'binance',
            '抛售': 'sell',
            '买入': 'buy',
            '持仓': 'position',
            'DeFi': 'defi',
            'NFT': 'nft',
            '代币': 'token',
            '项目': 'project',
            '分析': 'analysis',
            '市场': 'market',
            '价格': 'price',
            '投资': 'investment',
            '链上': 'onchain',
            '数据': 'data',
            '监控': 'monitoring',
            'USDT': 'usdt',
            'USDC': 'usdc'
        }
        
        # 提取关键词并转换为英文
        title_lower = chinese_title.lower()
        english_parts = []
        
        # 匹配关键术语
        for chinese, english in crypto_terms.items():
            if chinese.lower() in title_lower:
                english_parts.append(english)
        
        # 如果没有匹配到特定术语，使用通用描述
        if not english_parts:
            if '分析' in title_lower or '数据' in title_lower:
                english_parts.append('analysis')
            if '交易' in title_lower or '转账' in title_lower:
                english_parts.append('transaction')
            if '地址' in title_lower:
                english_parts.append('address')
        
        # 如果还是没有关键词，使用默认值
        if not english_parts:
            english_parts.append('crypto-data')
        
        # 去重并限制数量
        english_parts = list(dict.fromkeys(english_parts))[:3]
        
        # 生成slug
        slug_base = '-'.join(english_parts)
        slug = f"lookonchain-{slug_base}-{date_str}"
        
        # 清理slug（确保只包含字母、数字、连字符）
        slug = re.sub(r'[^a-z0-9\-]', '', slug.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        return slug

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
        
        # 生成英文slug
        slug = self.generate_english_slug(article['chinese_title'], now)
        
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
slug = '{slug}'
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
        
        # 首先尝试专业格式化
        if self.formatter and self.formatter.client:
            print("🎨 使用专业格式化器生成内容...")
            formatted_article = self.formatter.format_content(article)
            if formatted_article and formatted_article.get('formatted_content'):
                return self._add_author_section(formatted_article['formatted_content'])
        
        print("📝 使用默认格式生成内容...")
        # Fallback: 使用原有的简单格式
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
以上内容仅为链上数据分析，不构成投资建议。加密货币投资存在高风险，价格波动剧烈，请理性投资并做好风险管理。投资前请充分了解项目基本面，不要投入超出承受能力的资金。"""
        
        return self._add_author_section(content)
    
    def _add_author_section(self, content: str) -> str:
        """添加作者信息部分"""
        author_section = f"""

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
        
        return content + author_section
    
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
        content_history = self.load_content_history()
        
        print(f"📚 已生成文章数量: {len(generated_articles)}")
        print(f"📋 内容哈希记录数量: {len(content_history)}")
        
        # 确定输出目录
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        output_dir = os.path.join(current_dir, 'content', 'posts')
        
        generated_count = 0
        generated_files = []
        newly_generated = set()
        skipped_duplicates = 0
        
        for i, article in enumerate(processed_articles, 1):
            article_id = article['id']
            
            # 检查是否已生成
            if self.is_article_generated(article_id, generated_articles):
                print(f"⏭️ 跳过已生成文章 {i}: {article['chinese_title'][:30]}...")
                continue
            
            # 检查重复内容
            duplicate_info = self.is_duplicate_content(article, generated_articles, content_history)
            
            if duplicate_info['is_duplicate']:
                skipped_duplicates += 1
                print(f"🚫 跳过重复文章 {i}: {article['chinese_title'][:30]}...")
                continue
            
            print(f"\n📄 生成文章 {i}: {article['chinese_title'][:50]}...")
            
            # 生成文章
            file_path = self.create_hugo_article(article, output_dir)
            if file_path:
                generated_count += 1
                generated_files.append(file_path)
                newly_generated.add(article_id)
                
                # 添加到内容历史记录
                self.add_to_content_history(article, content_history)
                
                print(f"✅ 文章 {i} 生成成功")
            else:
                print(f"❌ 文章 {i} 生成失败")
        
        # 更新历史记录
        if newly_generated:
            all_generated = generated_articles.union(newly_generated)
            self.save_article_history(all_generated)
            
        # 保存内容历史记录
        if content_history:
            self.save_content_history(content_history)
        
        result = {
            "success": generated_count > 0,
            "generated": generated_count,
            "total_processed": len(processed_articles),
            "files": generated_files,
            "newly_generated_ids": list(newly_generated),
            "skipped_duplicates": skipped_duplicates
        }
        
        if generated_count > 0:
            result["message"] = f"成功生成 {generated_count} 篇文章，跳过 {skipped_duplicates} 篇重复文章"
        elif skipped_duplicates > 0:
            result["message"] = f"所有文章都是重复内容，跳过 {skipped_duplicates} 篇文章"
        else:
            result["message"] = "没有新文章生成（可能都已存在）"
        
        return result