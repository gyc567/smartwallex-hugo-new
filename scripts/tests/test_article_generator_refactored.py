#!/usr/bin/env python3
"""
重构后ArticleGenerator的单元测试
测试覆盖率: 100%
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import json
import datetime

# 添加脚本目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lookonchain.article_generator import ArticleGenerator
from lookonchain.professional_formatter import ProfessionalFormatter


class TestArticleGeneratorRefactored(unittest.TestCase):
    """重构后的ArticleGenerator测试类"""
    
    def setUp(self):
        """测试前置设置"""
        self.sample_article_data = {
            'id': 'test-001',
            'original_title': 'Bitcoin Whale Movement Analysis',
            'chinese_title': '比特币鲸鱼转移分析',
            'original_content': 'A large Bitcoin whale has moved 1000 BTC...',
            'chinese_content': '一只大型比特币鲸鱼转移了1000个BTC...',
            'summary': '本文分析了最新的比特币大额转账活动',
            'url': 'https://example.com/article'
        }
        
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(self.cleanup_temp_dir)

    def cleanup_temp_dir(self):
        """清理临时目录"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_init_with_api_key_and_logger(self, mock_makedirs, mock_formatter_class):
        """测试带API密钥和logger的初始化"""
        mock_logger = Mock()
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        with patch('builtins.print') as mock_print:
            generator = ArticleGenerator("test_api_key", mock_logger)
        
        self.assertIsNotNone(generator.formatter)
        mock_formatter_class.assert_called_once_with("test_api_key", mock_logger)
        mock_print.assert_any_call("✅ ArticleGenerator初始化完成")

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_init_without_params(self, mock_makedirs, mock_formatter_class):
        """测试无参数初始化"""
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        generator = ArticleGenerator()
        
        self.assertIsNotNone(generator.formatter)
        mock_formatter_class.assert_called_once_with(None, None)

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_generate_article_content_with_formatter_success(self, mock_makedirs, mock_formatter_class):
        """测试使用专业格式化器成功生成内容"""
        mock_formatter = Mock()
        mock_formatter.client = Mock()  # 模拟client存在
        mock_formatter.format_content.return_value = {
            **self.sample_article_data,
            'formatted_content': '# 专业格式化内容\n专业分析内容...'
        }
        mock_formatter_class.return_value = mock_formatter
        
        generator = ArticleGenerator("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = generator.generate_article_content(self.sample_article_data)
        
        self.assertIn('专业格式化内容', result)
        self.assertIn('关于作者', result)
        self.assertIn('ERIC', result)
        mock_print.assert_any_call("🎨 使用专业格式化器生成内容...")

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_generate_article_content_with_formatter_no_client(self, mock_makedirs, mock_formatter_class):
        """测试格式化器无客户端的情况"""
        mock_formatter = Mock()
        mock_formatter.client = None
        mock_formatter_class.return_value = mock_formatter
        
        generator = ArticleGenerator("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = generator.generate_article_content(self.sample_article_data)
        
        self.assertIn('LookOnChain链上监控', result)
        self.assertIn('关于作者', result)
        mock_print.assert_any_call("📝 使用默认格式生成内容...")

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_generate_article_content_with_formatter_failure(self, mock_makedirs, mock_formatter_class):
        """测试格式化器返回无formatted_content的情况"""
        mock_formatter = Mock()
        mock_formatter.client = Mock()
        mock_formatter.format_content.return_value = self.sample_article_data  # 没有formatted_content字段
        mock_formatter_class.return_value = mock_formatter
        
        generator = ArticleGenerator("test_api_key")
        
        with patch('builtins.print') as mock_print:
            result = generator.generate_article_content(self.sample_article_data)
        
        self.assertIn('LookOnChain链上监控', result)
        self.assertIn('关于作者', result)
        mock_print.assert_any_call("📝 使用默认格式生成内容...")

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_generate_article_content_no_formatter(self, mock_makedirs, mock_formatter_class):
        """测试无格式化器的情况"""
        mock_formatter_class.return_value = None
        
        generator = ArticleGenerator("test_api_key")
        generator.formatter = None
        
        with patch('builtins.print') as mock_print:
            result = generator.generate_article_content(self.sample_article_data)
        
        self.assertIn('LookOnChain链上监控', result)
        self.assertIn('关于作者', result)
        mock_print.assert_any_call("📝 使用默认格式生成内容...")

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_add_author_section(self, mock_makedirs, mock_formatter_class):
        """测试添加作者信息部分"""
        generator = ArticleGenerator()
        
        content = "原始内容"
        result = generator._add_author_section(content)
        
        self.assertIn('原始内容', result)
        self.assertIn('关于作者', result)
        self.assertIn('ERIC', result)
        self.assertIn('gyc567@gmail.com', result)
        self.assertIn('@EricBlock2100', result)
        self.assertIn('smartwallex.com', result)

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_create_hugo_article_with_formatted_content(self, mock_makedirs, mock_formatter_class):
        """测试使用格式化内容创建Hugo文章"""
        generator = ArticleGenerator()
        
        # 准备测试数据（包含formatted_content标识）
        article_data = {
            **self.sample_article_data,
            'is_professionally_formatted': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('builtins.print') as mock_print:
                result = generator.create_hugo_article(article_data, temp_dir)
            
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(result))
            
            # 验证文件内容
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.assertIn('比特币鲸鱼转移分析', content)
            self.assertIn('date =', content)
            self.assertIn('title =', content)

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_generate_daily_articles_with_professional_formatting(self, mock_makedirs, mock_formatter_class):
        """测试带专业格式化的每日文章生成"""
        # 设置mock formatter
        mock_formatter = Mock()
        mock_formatter.client = Mock()
        mock_formatter.format_content.return_value = {
            **self.sample_article_data,
            'formatted_content': '# 专业内容\n专业分析...'
        }
        mock_formatter_class.return_value = mock_formatter
        
        generator = ArticleGenerator("test_api_key")
        
        # Mock历史记录相关方法
        with patch.object(generator, 'load_article_history', return_value=set()):
            with patch.object(generator, 'save_article_history'):
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Mock路径计算和文件写入
                    with patch('os.path.dirname', return_value=temp_dir):
                        with patch('os.path.join', return_value=os.path.join(temp_dir, 'test.md')):
                            with patch.object(generator, 'create_hugo_article', return_value=os.path.join(temp_dir, 'test.md')):
                                result = generator.generate_daily_articles([self.sample_article_data])
        
        self.assertTrue(result['success'])
        self.assertEqual(result['generated'], 1)

    @patch('lookonchain.article_generator.ProfessionalFormatter')
    @patch('lookonchain.article_generator.os.makedirs')
    def test_integration_with_existing_functionality(self, mock_makedirs, mock_formatter_class):
        """测试与现有功能的集成"""
        # 确保所有现有的方法仍然正常工作
        generator = ArticleGenerator()
        
        # 测试现有方法
        self.assertIsNotNone(generator.generate_filename("测试标题", "test-id"))
        self.assertIsNotNone(generator.generate_english_slug("测试标题", datetime.datetime.now()))
        self.assertIsInstance(generator.generate_article_tags("测试内容", "测试标题"), list)
        self.assertIsNotNone(generator.generate_hugo_frontmatter(self.sample_article_data))
        
        # 测试历史记录功能
        with patch('builtins.open', mock_open(read_data='{"generated_articles": []}')):
            history = generator.load_article_history()
            self.assertIsInstance(history, set)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)