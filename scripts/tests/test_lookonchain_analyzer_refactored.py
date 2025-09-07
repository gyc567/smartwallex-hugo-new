#!/usr/bin/env python3
"""
重构后LookOnChainAnalyzer的单元测试
测试覆盖率: 100%
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lookonchain_analyzer import LookOnChainAnalyzer


class TestLookOnChainAnalyzerRefactored(unittest.TestCase):
    """重构后的LookOnChainAnalyzer测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.sample_raw_articles = [
            {
                'id': 'test-001',
                'title': 'Bitcoin Whale Movement',
                'content': 'A large Bitcoin whale has moved 1000 BTC...',
                'summary': 'Bitcoin whale analysis',
                'url': 'https://example.com/article1'
            }
        ]
        
        self.sample_processed_articles = [
            {
                'id': 'test-001',
                'original_title': 'Bitcoin Whale Movement',
                'chinese_title': '比特币鲸鱼转移分析',
                'original_content': 'A large Bitcoin whale has moved 1000 BTC...',
                'chinese_content': '一只大型比特币鲸鱼转移了1000个BTC...',
                'summary': '本文分析了最新的比特币大额转账活动',
                'url': 'https://example.com/article1',
                'processing_stats': {
                    'title_translation': True,
                    'content_translation': True,
                    'summary_generation': True
                }
            }
        ]

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')  
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_init_with_api_key(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试带API密钥的初始化"""
        mock_scraper = Mock()
        mock_translator = Mock()
        mock_translator.logger = Mock()
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        with patch('builtins.print') as mock_print:
            analyzer = LookOnChainAnalyzer("test_api_key")
        
        self.assertEqual(analyzer.openai_api_key, "test_api_key")
        self.assertEqual(analyzer.scraper, mock_scraper)
        self.assertEqual(analyzer.translator, mock_translator)
        self.assertEqual(analyzer.generator, mock_generator)
        
        # 验证generator初始化时传递了正确的参数
        mock_generator_class.assert_called_once_with("test_api_key", mock_translator.logger)
        mock_print.assert_any_call("🚀 LookOnChain 分析器初始化完成")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_init_without_api_key(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试无API密钥的初始化（使用环境变量）"""
        mock_scraper = Mock()
        mock_translator = Mock()
        mock_translator.logger = None  # 翻译器无logger的情况
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        with patch('lookonchain_analyzer.OPENAI_API_KEY', 'env_api_key'):
            analyzer = LookOnChainAnalyzer()
        
        self.assertEqual(analyzer.openai_api_key, 'env_api_key')
        mock_generator_class.assert_called_once_with('env_api_key', None)

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_init_translator_is_none(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试翻译器为None的情况"""
        mock_scraper = Mock()
        mock_translator = None
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        # 验证generator初始化时处理了translator为None的情况
        mock_generator_class.assert_called_once_with("test_api_key", None)

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_success_with_professional_formatting(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试带专业格式化的每日分析成功执行"""
        # 设置mocks
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = self.sample_raw_articles
        
        mock_translator = Mock()
        mock_translator.client = Mock()  # 确保有客户端
        mock_translator.logger = Mock()
        mock_translator.process_article.return_value = self.sample_processed_articles[0]
        
        mock_generator = Mock()
        mock_generator.generate_daily_articles.return_value = {
            "success": True,
            "generated": 1,
            "total_processed": 1,
            "files": ["/path/to/generated/article.md"],
            "message": "成功生成 1 篇文章"
        }
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = analyzer.run_daily_analysis()
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["scrapped_articles"], 1)
        self.assertEqual(result["translated_articles"], 1)
        self.assertEqual(result["generated_articles"], 1)
        self.assertEqual(result["stage"], "completed")
        
        # 验证调用链
        mock_scraper.scrape_top_articles.assert_called_once()
        mock_translator.process_article.assert_called_once()
        mock_generator.generate_daily_articles.assert_called_once()

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_scraping_failure(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试爬取失败的情况"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = []
        
        mock_translator = Mock()
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "未能爬取到任何文章")
        self.assertEqual(result["stage"], "scraping")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_translation_client_not_initialized(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试翻译客户端未初始化的情况"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = self.sample_raw_articles
        
        mock_translator = Mock()
        mock_translator.client = None  # 客户端未初始化
        
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "翻译客户端未初始化，请检查OPENAI_API_KEY")
        self.assertEqual(result["stage"], "translation_init")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_all_translation_failures(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试所有文章翻译都失败的情况"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = self.sample_raw_articles
        
        mock_translator = Mock()
        mock_translator.client = Mock()
        mock_translator.process_article.return_value = None  # 翻译失败
        
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        with patch('lookonchain_analyzer.MAX_ARTICLES_PER_DAY', 1):
            result = analyzer.run_daily_analysis()
        
        self.assertFalse(result["success"])
        self.assertIn("所有", result["error"])
        self.assertIn("篇文章处理均失败", result["error"])
        self.assertEqual(result["stage"], "translation")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_partial_failures(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试部分文章处理失败的情况"""
        # 准备多个文章，部分成功部分失败
        raw_articles = self.sample_raw_articles + [
            {
                'id': 'test-002',
                'title': 'Another Article',
                'content': 'Content...',
                'summary': 'Summary',
                'url': 'https://example.com/article2'
            }
        ]
        
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = raw_articles
        
        mock_translator = Mock()
        mock_translator.client = Mock()
        # 第一个成功，第二个失败
        mock_translator.process_article.side_effect = [self.sample_processed_articles[0], None]
        
        mock_generator = Mock()
        mock_generator.generate_daily_articles.return_value = {
            "success": True,
            "generated": 1,
            "total_processed": 1,
            "files": ["/path/to/article.md"],
            "message": "成功生成 1 篇文章"
        }
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = analyzer.run_daily_analysis()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["failed_articles"], 1)
        self.assertEqual(result["translated_articles"], 1)

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_generation_failure(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试文章生成失败的情况"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = self.sample_raw_articles
        
        mock_translator = Mock()
        mock_translator.client = Mock()
        mock_translator.process_article.return_value = self.sample_processed_articles[0]
        
        mock_generator = Mock()
        mock_generator.generate_daily_articles.return_value = {
            "success": False,
            "generated": 0,
            "total_processed": 1,
            "files": [],
            "message": "文章生成失败"
        }
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "文章生成失败")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_exception_handling(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试异常处理"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.side_effect = Exception("网络错误")
        
        mock_translator = Mock()
        mock_generator = Mock()
        
        mock_scraper_class.return_value = mock_scraper
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result["success"])
        self.assertIn("执行过程中发生错误", result["error"])
        self.assertEqual(result["stage"], "execution")

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_print_summary_success(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试成功结果摘要打印"""
        mock_translator = Mock()
        mock_translator.logger = Mock()
        mock_translator.get_api_usage_stats.return_value = {
            'total_calls': 10,
            'successful_calls': 9,
            'failed_calls': 1,
            'total_tokens': 5000
        }
        
        mock_scraper_class.return_value = Mock()
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = Mock()
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        success_result = {
            "success": True,
            "scrapped_articles": 3,
            "translated_articles": 3,
            "generated_articles": 3,
            "failed_articles": 0,
            "message": "成功生成 3 篇文章",
            "generated_files": ["/path/to/article1.md", "/path/to/article2.md"],
            "execution_time": "2024-01-01T12:00:00"
        }
        
        with patch('builtins.print') as mock_print:
            analyzer.print_summary(success_result)
        
        # 验证打印了成功信息
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_prints = [p for p in print_calls if "任务执行成功" in p]
        self.assertTrue(len(success_prints) > 0)

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_print_summary_failure(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试失败结果摘要打印"""
        mock_translator = Mock()
        mock_translator.logger = None  # 无logger
        
        mock_scraper_class.return_value = Mock()
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = Mock()
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        failure_result = {
            "success": False,
            "stage": "scraping",
            "error": "网络连接失败",
            "execution_time": "2024-01-01T12:00:00"
        }
        
        with patch('builtins.print') as mock_print:
            analyzer.print_summary(failure_result)
        
        # 验证打印了失败信息
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        failure_prints = [p for p in print_calls if "任务执行失败" in p]
        self.assertTrue(len(failure_prints) > 0)

    @patch('lookonchain_analyzer.ArticleGenerator')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_print_summary_with_api_stats_error(self, mock_scraper_class, mock_translator_class, mock_generator_class):
        """测试API统计信息获取错误的情况"""
        mock_translator = Mock()
        mock_translator.logger = Mock()
        mock_translator.get_api_usage_stats.return_value = {"error": "无法获取统计"}
        
        mock_scraper_class.return_value = Mock()
        mock_translator_class.return_value = mock_translator
        mock_generator_class.return_value = Mock()
        
        analyzer = LookOnChainAnalyzer("test_api_key")
        
        result = {"success": True, "execution_time": "2024-01-01T12:00:00"}
        
        with patch('builtins.print') as mock_print:
            analyzer.print_summary(result)
        
        # 验证打印了错误信息
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_prints = [p for p in print_calls if "无法获取统计" in p]
        self.assertTrue(len(error_prints) > 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)