#!/usr/bin/env python3
"""
LookOnChain 增强处理器单元测试
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

from lookonchain.enhanced_processor import EnhancedArticleProcessor


class TestEnhancedArticleProcessor(unittest.TestCase):
    """增强处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.temp_dir, 'test_history.json')
        
        # Mock OpenAI client
        self.mock_client = MagicMock()
        
        # 创建处理器实例
        with patch('openai_client.OpenAIClientWrapper') as mock_openai:
            mock_openai.return_value = self.mock_client
            self.processor = EnhancedArticleProcessor('test_api_key')
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.processor.client)
        self.assertIsNotNone(self.processor.history_manager)
        self.assertEqual(self.processor.api_calls['translation'], 0)
        self.assertEqual(self.processor.api_calls['summary'], 0)
    
    def test_translate_article_success(self):
        """测试翻译成功"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        result = self.processor.translate_article('Test Title', 'Test Content')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['title'], '测试标题')
        self.assertEqual(result['content'], '测试内容')
        self.assertEqual(self.processor.api_calls['translation'], 1)
    
    def test_translate_article_json_parse_failure(self):
        """测试翻译JSON解析失败"""
        # Mock API返回无效JSON
        self.mock_client.chat_completion.return_value = {
            'choices': [{
                'message': {
                    'content': 'Invalid JSON response'
                }
            }]
        }
        
        result = self.processor.translate_article('Test Title', 'Test Content')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['title'], 'Test Title')  # 使用原标题
        self.assertEqual(result['content'], 'Invalid JSON response')
        self.assertEqual(self.processor.api_calls['translation'], 1)
    
    def test_translate_article_api_failure(self):
        """测试翻译API失败"""
        # Mock API异常
        self.mock_client.chat_completions_create.side_effect = Exception("API Error")
        
        result = self.processor.translate_article('Test Title', 'Test Content')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['title'], 'Test Title')
        self.assertEqual(result['content'], 'Test Content')
        self.assertEqual(self.processor.api_calls['failed'], 1)
    
    def test_generate_ai_summary_success(self):
        """测试AI摘要生成成功"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': '这是一个测试摘要'
                }
            }]
        }
        
        result = self.processor.generate_ai_summary('Test Title', 'Test Content')
        
        self.assertEqual(result, '这是一个测试摘要')
        self.assertEqual(self.processor.api_calls['summary'], 1)
    
    def test_generate_ai_summary_api_failure(self):
        """测试AI摘要生成API失败"""
        # Mock API异常
        self.mock_client.chat_completions_create.side_effect = Exception("API Error")
        
        result = self.processor.generate_ai_summary('Test Title', 'Test Content')
        
        self.assertEqual(result, '')
        self.assertEqual(self.processor.api_calls['failed'], 1)
    
    def test_process_article_success(self):
        """测试处理文章成功"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        article = {
            'title': 'Test Title',
            'content': 'Test Content',
            'url': 'https://example.com/test'
        }
        
        result = self.processor.process_article(article)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], '测试标题')
        self.assertEqual(result['content'], '测试内容')
        self.assertTrue(result['translation_success'])
        self.assertTrue(result['has_summary'])
        self.assertEqual(result['original_title'], 'Test Title')
        self.assertEqual(result['original_content'], 'Test Content')
    
    def test_process_article_duplicate(self):
        """测试处理重复文章"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        article = {
            'title': 'Test Title',
            'content': 'Test Content',
            'url': 'https://example.com/test'
        }
        
        # 第一次处理
        result1 = self.processor.process_article(article)
        self.assertIsNotNone(result1)
        
        # 第二次处理（应该被识别为重复）
        result2 = self.processor.process_article(article)
        self.assertIsNone(result2)
    
    def test_process_article_incomplete_info(self):
        """测试处理信息不完整的文章"""
        article = {
            'title': '',  # 空标题
            'content': 'Test Content',
            'url': 'https://example.com/test'
        }
        
        result = self.processor.process_article(article)
        self.assertIsNone(result)
    
    def test_process_articles_batch(self):
        """测试批量处理文章"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        articles = [
            {
                'title': 'Test Title 1',
                'content': 'Test Content 1',
                'url': 'https://example.com/test1'
            },
            {
                'title': 'Test Title 2',
                'content': 'Test Content 2',
                'url': 'https://example.com/test2'
            }
        ]
        
        result = self.processor.process_articles_batch(articles)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], '测试标题')
        self.assertEqual(result[1]['title'], '测试标题')
    
    def test_process_articles_batch_with_duplicates(self):
        """测试批量处理包含重复文章"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        articles = [
            {
                'title': 'Test Title 1',
                'content': 'Test Content 1',
                'url': 'https://example.com/test1'
            },
            {
                'title': 'Test Title 1',  # 重复标题
                'content': 'Different Content',
                'url': 'https://example.com/test2'
            }
        ]
        
        result = self.processor.process_articles_batch(articles)
        
        # 应该只有1篇，因为第2篇标题重复
        self.assertEqual(len(result), 1)
    
    def test_get_api_statistics(self):
        """测试获取API统计"""
        # Mock API响应
        self.mock_client.chat_completions_create.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'title': '测试标题',
                        'content': '测试内容'
                    })
                }
            }]
        }
        
        # 执行一些API调用
        self.processor.translate_article('Test Title', 'Test Content')
        self.processor.generate_ai_summary('Test Title', 'Test Content')
        
        stats = self.processor.get_api_statistics()
        
        self.assertEqual(stats['translation_calls'], 1)
        self.assertEqual(stats['summary_calls'], 1)
        self.assertEqual(stats['failed_calls'], 0)
        self.assertEqual(stats['total_calls'], 2)
        self.assertEqual(stats['success_rate'], 1.0)
    
    def test_process_article_exception_handling(self):
        """测试处理文章异常处理"""
        # Mock API异常
        self.mock_client.chat_completions_create.side_effect = Exception("API Error")
        
        article = {
            'title': 'Test Title',
            'content': 'Test Content',
            'url': 'https://example.com/test'
        }
        
        result = self.processor.process_articles_batch([article])
        
        # 应该返回空列表，因为处理失败
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()