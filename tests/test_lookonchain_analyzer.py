#!/usr/bin/env python3
"""
LookOnChain 主分析器单元测试
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

from lookonchain_analyzer import LookOnChainAnalyzer


class TestLookOnChainAnalyzer(unittest.TestCase):
    """主分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.content_dir = os.path.join(self.temp_dir, 'content', 'posts')
        os.makedirs(self.content_dir, exist_ok=True)
        
        # Mock组件
        self.mock_scraper = MagicMock()
        self.mock_processor = MagicMock()
        
        # 创建分析器实例
        with patch('lookonchain_enhanced_scraper.EnhancedLookOnChainScraper') as mock_scraper_class:
            with patch('lookonchain_enhanced_processor.EnhancedArticleProcessor') as mock_processor_class:
                
                mock_scraper_class.return_value = self.mock_scraper
                mock_processor_class.return_value = self.mock_processor
                
                self.analyzer = LookOnChainAnalyzer('test_api_key')
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.analyzer.scraper)
        self.assertIsNotNone(self.analyzer.processor)
    
    def test_run_daily_analysis_success(self):
        """测试每日分析成功"""
        # Mock爬虫返回
        raw_articles = [
            {
                'title': 'Test Article 1',
                'content': 'Test content 1',
                'url': 'https://example.com/article1'
            },
            {
                'title': 'Test Article 2',
                'content': 'Test content 2',
                'url': 'https://example.com/article2'
            }
        ]
        self.mock_scraper.scrape_latest_articles.return_value = raw_articles
        
        # Mock处理器返回
        processed_articles = [
            {
                'title': '测试文章 1',
                'content': '测试内容 1',
                'summary': '测试摘要 1',
                'url': 'https://example.com/article1',
                'original_title': 'Test Article 1',
                'original_content': 'Test content 1'
            },
            {
                'title': '测试文章 2',
                'content': '测试内容 2',
                'summary': '测试摘要 2',
                'url': 'https://example.com/article2',
                'original_title': 'Test Article 2',
                'original_content': 'Test content 2'
            }
        ]
        self.mock_processor.process_articles_batch.return_value = processed_articles
        self.mock_processor.get_api_statistics.return_value = {
            'translation_calls': 2,
            'summary_calls': 2,
            'failed_calls': 0,
            'total_calls': 4,
            'success_rate': 1.0
        }
        
        # Mock统计打印
        self.mock_processor.print_history_statistics.return_value = None
        
        result = self.analyzer.run_daily_analysis()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['scrapped_articles'], 2)
        self.assertEqual(result['processed_articles'], 2)
        self.assertEqual(result['unique_articles'], 2)
        self.assertIn('api_stats', result)
        self.assertEqual(result['stage'], 'completed')
    
    def test_run_daily_analysis_scraping_failure(self):
        """测试爬取失败"""
        self.mock_scraper.scrape_latest_articles.return_value = []
        self.mock_processor.print_history_statistics.return_value = None
        
        result = self.analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], '未能爬取到任何文章')
        self.assertEqual(result['stage'], 'scraping')
    
    def test_run_daily_analysis_processing_failure(self):
        """测试处理失败"""
        # Mock爬虫返回
        raw_articles = [
            {
                'title': 'Test Article 1',
                'content': 'Test content 1',
                'url': 'https://example.com/article1'
            }
        ]
        self.mock_scraper.scrape_latest_articles.return_value = raw_articles
        
        # Mock处理器返回空列表
        self.mock_processor.process_articles_batch.return_value = []
        self.mock_processor.print_history_statistics.return_value = None
        
        result = self.analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], '所有文章处理均失败或重复')
        self.assertEqual(result['stage'], 'processing')
    
    def test_run_daily_analysis_exception(self):
        """测试异常处理"""
        self.mock_scraper.scrape_latest_articles.side_effect = Exception("Test Exception")
        self.mock_processor.print_history_statistics.return_value = None
        
        result = self.analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], '执行过程中发生错误: Test Exception')
        self.assertEqual(result['stage'], 'execution')
    
    def test_save_processed_articles_success(self):
        """测试保存处理后的文章成功"""
        processed_articles = [
            {
                'title': '测试文章 1',
                'content': '测试内容 1',
                'summary': '测试摘要 1',
                'url': 'https://example.com/article1',
                'original_title': 'Test Article 1',
                'original_content': 'Test content 1'
            }
        ]
        
        # Mock内容目录
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', mock_open()) as mock_file:
                result = self.analyzer._save_processed_articles(processed_articles)
                
                self.assertTrue(result['success'])
                self.assertEqual(len(result['generated_files']), 1)
                self.assertIn('成功生成 1 篇文章', result['message'])
    
    def test_save_processed_articles_failure(self):
        """测试保存处理后的文章失败"""
        processed_articles = [
            {
                'title': '测试文章 1',
                'content': '测试内容 1',
                'summary': '测试摘要 1',
                'url': 'https://example.com/article1',
                'original_title': 'Test Article 1',
                'original_content': 'Test content 1'
            }
        ]
        
        # Mock文件操作异常
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', side_effect=OSError("Permission denied")):
                result = self.analyzer._save_processed_articles(processed_articles)
                
                self.assertFalse(result['success'])
                self.assertIn('保存文章失败', result['message'])
    
    def test_generate_hugo_content(self):
        """测试生成Hugo内容"""
        article = {
            'title': '测试文章',
            'content': '这是测试内容',
            'summary': '这是测试摘要',
            'url': 'https://example.com/article',
            'original_title': 'Test Article'
        }
        
        result = self.analyzer._generate_hugo_content(article)
        
        self.assertIn('---', result)
        self.assertIn('title: 测试文章', result)
        self.assertIn('description: 这是测试摘要', result)
        self.assertIn('tags:', result)
        self.assertIn('LookOnChain', result)
        self.assertIn('AI摘要', result)
        self.assertIn('## 🤖 AI摘要', result)
        self.assertIn('## 📝 原文翻译', result)
        self.assertIn('这是测试摘要', result)
        self.assertIn('这是测试内容', result)
        self.assertIn('原文链接', result)
        self.assertIn('Test Article', result)
    
    def test_generate_hugo_content_no_summary(self):
        """测试生成Hugo内容（无摘要）"""
        article = {
            'title': '测试文章',
            'content': '这是测试内容',
            'url': 'https://example.com/article',
            'original_title': 'Test Article'
        }
        
        result = self.analyzer._generate_hugo_content(article)
        
        self.assertIn('---', result)
        self.assertIn('title: 测试文章', result)
        self.assertNotIn('AI摘要', result)
        self.assertNotIn('## 🤖 AI摘要', result)
        self.assertIn('## 📝 原文翻译', result)
    
    def test_print_summary_success(self):
        """测试打印成功摘要"""
        result = {
            'success': True,
            'scrapped_articles': 2,
            'processed_articles': 2,
            'unique_articles': 2,
            'generated_articles': ['/path/to/file1.md', '/path/to/file2.md'],
            'message': '成功生成 2 篇文章',
            'api_stats': {
                'translation_calls': 2,
                'summary_calls': 2,
                'failed_calls': 0,
                'success_rate': 1.0
            },
            'execution_time': '2025-01-22T10:00:00'
        }
        
        # 这个方法不应该抛出异常
        self.analyzer.print_summary(result)
    
    def test_print_summary_failure(self):
        """测试打印失败摘要"""
        result = {
            'success': False,
            'error': '测试错误',
            'stage': 'scraping',
            'execution_time': '2025-01-22T10:00:00'
        }
        
        # 这个方法不应该抛出异常
        self.analyzer.print_summary(result)
    
    def test_print_summary_no_api_stats(self):
        """测试打印无API统计的摘要"""
        result = {
            'success': True,
            'scrapped_articles': 1,
            'processed_articles': 1,
            'unique_articles': 1,
            'generated_articles': ['/path/to/file1.md'],
            'message': '成功生成 1 篇文章',
            'execution_time': '2025-01-22T10:00:00'
        }
        
        # 这个方法不应该抛出异常
        self.analyzer.print_summary(result)


if __name__ == '__main__':
    unittest.main()