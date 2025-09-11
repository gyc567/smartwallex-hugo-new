#!/usr/bin/env python3
"""
LookOnChain 历史文章管理模块
负责存储和管理已处理的文章，确保内容去重
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Set
from .config import LOOKONCHAIN_HISTORY_FILE, DATA_DIR


class ArticleHistoryManager:
    """历史文章管理器"""
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file or LOOKONCHAIN_HISTORY_FILE
        self.articles_data = self._load_history()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
    
    def _load_history(self) -> Dict:
        """加载历史数据"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ 成功加载历史数据，包含 {len(data.get('articles', []))} 篇文章")
                return data
            except Exception as e:
                print(f"⚠️ 加载历史数据失败: {e}")
                return self._create_empty_history()
        else:
            print("📝 创建新的历史数据文件")
            return self._create_empty_history()
    
    def _create_empty_history(self) -> Dict:
        """创建空的历史数据结构"""
        return {
            "last_updated": datetime.now().isoformat(),
            "total_articles": 0,
            "articles": []
        }
    
    def _save_history(self):
        """保存历史数据"""
        try:
            self.articles_data["last_updated"] = datetime.now().isoformat()
            self.articles_data["total_articles"] = len(self.articles_data["articles"])
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.articles_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功保存历史数据，共 {self.articles_data['total_articles']} 篇文章")
        except Exception as e:
            print(f"❌ 保存历史数据失败: {e}")
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希值用于去重"""
        # 清理内容：移除多余的空白和标点
        import re
        cleaned_content = re.sub(r'\s+', ' ', content.strip())
        # 移除常见的标点符号差异
        cleaned_content = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned_content)
        # 转换为小写进行比较
        cleaned_content = cleaned_content.lower()
        
        return hashlib.md5(cleaned_content.encode('utf-8')).hexdigest()
    
    def _generate_title_hash(self, title: str) -> str:
        """生成标题哈希值"""
        # 清理标题
        import re
        cleaned_title = re.sub(r'\s+', ' ', title.strip())
        cleaned_title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned_title)
        cleaned_title = cleaned_title.lower()
        
        return hashlib.md5(cleaned_title.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, article: Dict) -> bool:
        """检查文章是否重复"""
        title_hash = self._generate_title_hash(article.get('title', ''))
        content_hash = self._generate_content_hash(article.get('content', ''))
        
        for existing_article in self.articles_data["articles"]:
            existing_title_hash = existing_article.get('title_hash')
            existing_content_hash = existing_article.get('content_hash')
            
            # 标题完全相同认为是重复
            if title_hash == existing_title_hash:
                print(f"🔍 发现重复标题: {article.get('title', 'N/A')}")
                return True
            
            # 内容相似度超过90%认为是重复
            if content_hash == existing_content_hash:
                print(f"🔍 发现重复内容: {article.get('title', 'N/A')}")
                return True
        
        return False
    
    def add_article(self, article: Dict) -> bool:
        """添加文章到历史记录"""
        if self.is_duplicate(article):
            return False
        
        article_record = {
            "title": article.get('title', ''),
            "url": article.get('url', ''),
            "title_hash": self._generate_title_hash(article.get('title', '')),
            "content_hash": self._generate_content_hash(article.get('content', '')),
            "processed_date": datetime.now().isoformat(),
            "content_length": len(article.get('content', ''))
        }
        
        self.articles_data["articles"].append(article_record)
        self._save_history()
        
        print(f"📝 添加文章到历史记录: {article.get('title', 'N/A')[:50]}...")
        return True
    
    def add_articles_batch(self, articles: List[Dict]) -> List[Dict]:
        """批量添加文章，返回非重复的文章"""
        unique_articles = []
        
        for article in articles:
            if not self.is_duplicate(article):
                self.add_article(article)
                unique_articles.append(article)
            else:
                print(f"⚠️ 跳过重复文章: {article.get('title', 'N/A')[:50]}...")
        
        print(f"📊 批量添加完成: {len(unique_articles)}/{len(articles)} 篇文章为新文章")
        return unique_articles
    
    def get_recent_articles(self, days: int = 7) -> List[Dict]:
        """获取最近N天的文章"""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
        
        recent_articles = []
        for article in self.articles_data["articles"]:
            processed_date = datetime.fromisoformat(article["processed_date"])
            if processed_date >= cutoff_date:
                recent_articles.append(article)
        
        return recent_articles
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_articles = len(self.articles_data["articles"])
        
        # 计算最近7天的文章数量
        recent_articles = self.get_recent_articles(7)
        
        # 计算内容长度统计
        content_lengths = [article["content_length"] for article in self.articles_data["articles"]]
        avg_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        return {
            "total_articles": total_articles,
            "recent_7_days": len(recent_articles),
            "average_content_length": round(avg_length, 0),
            "last_updated": self.articles_data["last_updated"]
        }
    
    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        
        print("📊 LookOnChain 历史文章统计")
        print("=" * 50)
        print(f"📚 总文章数: {stats['total_articles']}")
        print(f"📅 最近7天: {stats['recent_7_days']} 篇")
        print(f"📝 平均内容长度: {stats['average_content_length']} 字符")
        print(f"🕐 最后更新: {stats['last_updated']}")
        print("=" * 50)
    
    def clear_old_articles(self, days: int = 30):
        """清理超过指定天数的旧文章"""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        cutoff_date = cutoff_date - timedelta(days=days)
        
        original_count = len(self.articles_data["articles"])
        
        self.articles_data["articles"] = [
            article for article in self.articles_data["articles"]
            if datetime.fromisoformat(article["processed_date"]) >= cutoff_date
        ]
        
        removed_count = original_count - len(self.articles_data["articles"])
        
        if removed_count > 0:
            self._save_history()
            print(f"🧹 已清理 {removed_count} 篇超过 {days} 天的旧文章")
        else:
            print(f"📝 没有需要清理的旧文章")