#!/usr/bin/env python3
"""
LookOnChain 历史管理器单元测试
"""

import unittest
import tempfile
import os
import json
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

from lookonchain.history_manager import ArticleHistoryManager


class TestArticleHistoryManager(unittest.TestCase):
    """历史管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.json')
        self.manager = ArticleHistoryManager(self.history_file)
        
        # 确保历史文件被创建
        self.manager._save_history()
        
        # 测试文章数据
        self.test_articles = [
            {
                'title': 'Test Article 1',
                'content': 'This is test content for article 1',
                'url': 'https://example.com/article1'
            },
            {
                'title': 'Test Article 2',
                'content': 'This is different content for article 2',
                'url': 'https://example.com/article2'
            },
            {
                'title': 'Test Article 1',  # 重复标题
                'content': 'This is different content but same title',
                'url': 'https://example.com/article3'
            }
        ]
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_init_creates_history_file(self):
        """测试初始化时创建历史文件"""
        self.assertTrue(os.path.exists(self.history_file))
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIn('articles', data)
        self.assertIn('last_updated', data)
        self.assertIn('total_articles', data)
        self.assertEqual(data['total_articles'], 0)
    
    def test_add_article(self):
        """测试添加文章"""
        article = self.test_articles[0]
        
        result = self.manager.add_article(article)
        self.assertTrue(result)
        
        # 检查文件是否保存
        with open(self.history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(len(data['articles']), 1)
        self.assertEqual(data['articles'][0]['title'], article['title'])
        self.assertEqual(data['total_articles'], 1)
    
    def test_is_duplicate_title(self):
        """测试标题重复检测"""
        article = self.test_articles[0]
        
        # 添加第一篇文章
        self.manager.add_article(article)
        
        # 检查相同标题的文章
        duplicate_article = {
            'title': 'Test Article 1',
            'content': 'Different content',
            'url': 'https://example.com/different'
        }
        
        self.assertTrue(self.manager.is_duplicate(duplicate_article))
    
    def test_is_duplicate_content(self):
        """测试内容重复检测"""
        article = self.test_articles[0]
        
        # 添加第一篇文章
        self.manager.add_article(article)
        
        # 检查相同内容的文章
        duplicate_article = {
            'title': 'Different Title',
            'content': 'This is test content for article 1',
            'url': 'https://example.com/different'
        }
        
        self.assertTrue(self.manager.is_duplicate(duplicate_article))
    
    def test_is_not_duplicate(self):
        """测试非重复文章"""
        article1 = self.test_articles[0]
        article2 = self.test_articles[1]
        
        # 添加第一篇文章
        self.manager.add_article(article1)
        
        # 检查不同的文章
        self.assertFalse(self.manager.is_duplicate(article2))
    
    def test_add_articles_batch(self):
        """测试批量添加文章"""
        result = self.manager.add_articles_batch(self.test_articles)
        
        # 应该只有2篇，因为第3篇标题重复
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Test Article 1')
        self.assertEqual(result[1]['title'], 'Test Article 2')
    
    def test_get_recent_articles(self):
        """测试获取最近文章"""
        # 添加文章
        self.manager.add_article(self.test_articles[0])
        self.manager.add_article(self.test_articles[1])
        
        # 获取最近7天的文章
        recent = self.manager.get_recent_articles(7)
        self.assertEqual(len(recent), 2)
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加文章
        self.manager.add_article(self.test_articles[0])
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['total_articles'], 1)
        self.assertEqual(stats['recent_7_days'], 1)
        self.assertGreater(stats['average_content_length'], 0)
        self.assertIn('last_updated', stats)
    
    def test_clear_old_articles(self):
        """测试清理旧文章"""
        # 直接创建一个旧文章
        old_date = datetime.now() - timedelta(days=35)
        
        # 直接操作数据
        self.manager.articles_data['articles'] = [{
            'title': 'Old Article',
            'url': 'https://example.com/old',
            'processed_date': old_date.isoformat(),
            'content_length': 100
        }]
        
        # 验证文章确实是旧的
        self.assertEqual(len(self.manager.articles_data['articles']), 1)
        
        # 清理30天前的文章
        self.manager.clear_old_articles(30)
        
        # 检查是否已清理
        self.assertEqual(len(self.manager.articles_data['articles']), 0)
    
    def test_content_hash_generation(self):
        """测试内容哈希生成"""
        content1 = "This is test content"
        content2 = "This is test content  "  # 额外空格
        content3 = "This is test content!"  # 标点符号差异
        
        # 清理后的内容应该产生相同的哈希
        hash1 = self.manager._generate_content_hash(content1)
        hash2 = self.manager._generate_content_hash(content2)
        hash3 = self.manager._generate_content_hash(content3)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash1, hash3)
    
    def test_title_hash_generation(self):
        """测试标题哈希生成"""
        title1 = "Test Title"
        title2 = "test title"  # 大小写差异
        title3 = "Test Title!"  # 标点符号差异
        
        # 清理后的标题应该产生相同的哈希
        hash1 = self.manager._generate_title_hash(title1)
        hash2 = self.manager._generate_title_hash(title2)
        hash3 = self.manager._generate_title_hash(title3)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(hash1, hash3)


if __name__ == '__main__':
    unittest.main()