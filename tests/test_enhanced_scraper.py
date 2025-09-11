#!/usr/bin/env python3
"""
LookOnChain 增强爬虫单元测试
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from bs4 import BeautifulSoup
import requests

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

from lookonchain.enhanced_scraper import EnhancedLookOnChainScraper


class TestEnhancedLookOnChainScraper(unittest.TestCase):
    """增强爬虫测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.scraper = EnhancedLookOnChainScraper()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.scraper.session)
        self.assertIsNotNone(self.scraper.cache)
        self.assertEqual(self.scraper.cache_timeout, 300)
    
    def test_cache_operations(self):
        """测试缓存操作"""
        # 测试缓存有效性
        cache_key = "test_key"
        mock_response = MagicMock()
        
        # 测试初始状态
        self.assertFalse(self.scraper._is_cache_valid(cache_key))
        self.assertIsNone(self.scraper._get_cached_response(cache_key))
        
        # 测试缓存设置
        self.scraper._cache_response(cache_key, mock_response)
        self.assertTrue(self.scraper._is_cache_valid(cache_key))
        cached_response = self.scraper._get_cached_response(cache_key)
        self.assertIsNotNone(cached_response)
    
    @patch('requests.Session.get')
    def test_get_latest_articles_page_success(self, mock_get):
        """测试获取最新文章页面成功"""
        mock_response = MagicMock()
        mock_response.content = '''
        <html>
            <div id="index_feeds_list">
                <a href="/articles/test1">Test Article 1</a>
                <a href="/articles/test2">Test Article 2</a>
            </div>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.get_latest_articles_page()
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, BeautifulSoup)
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_get_latest_articles_page_failure(self, mock_get):
        """测试获取最新文章页面失败"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection Error")
        
        result = self.scraper.get_latest_articles_page()
        
        self.assertIsNone(result)
    
    def test_extract_latest_article_links_success(self):
        """测试提取最新文章链接成功"""
        html_content = '''
        <html>
            <div id="index_feeds_list">
                <a href="/articles/test1">Test Article 1 Title</a>
                <a href="/articles/test2">Test Article 2 Title</a>
            </div>
        </html>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = self.scraper.extract_latest_article_links(soup)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Test Article 1 Title')
        self.assertEqual(result[1]['title'], 'Test Article 2 Title')
        self.assertTrue(result[0]['url'].endswith('/articles/test1'))
        self.assertTrue(result[1]['url'].endswith('/articles/test2'))
    
    def test_extract_latest_article_links_no_articles(self):
        """测试没有文章链接的情况"""
        html_content = '''
        <html>
            <div>
                <p>No articles here</p>
            </div>
        </html>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = self.scraper.extract_latest_article_links(soup)
        
        self.assertEqual(len(result), 0)
    
    def test_parse_article_element_success(self):
        """测试解析文章元素成功"""
        html_content = '<a href="/articles/test">Test Article Title</a>'
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.find('a')
        
        result = self.scraper._parse_article_element(element, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test Article Title')
        self.assertTrue(result['url'].endswith('/articles/test'))
        self.assertEqual(result['index'], 0)
    
    def test_parse_article_element_invalid(self):
        """测试解析无效文章元素"""
        html_content = '<span>No link here</span>'
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.find('span')
        
        result = self.scraper._parse_article_element(element, 0)
        
        self.assertIsNone(result)
    
    def test_clean_title(self):
        """测试标题清理"""
        dirty_title = "2025.01.22 Test Article Title - Some Extra Text"
        clean_title = self.scraper._clean_title(dirty_title)
        
        self.assertNotIn("2025.01.22", clean_title)
        self.assertEqual(clean_title, "Test Article Title Some Extra Text")
    
    def test_extract_publish_time(self):
        """测试提取发布时间"""
        html_content = '''
        <div>
            <span class="date">2025.01.22</span>
            <a href="/articles/test">Test Article</a>
        </div>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        element = soup.find('div')
        
        result = self.scraper._extract_publish_time(element)
        
        self.assertEqual(result, "2025.01.22")
    
    def test_sort_articles_by_date(self):
        """测试按日期排序文章"""
        articles = [
            {'title': 'Article 1', 'publish_time': '2025.01.20', 'index': 0},
            {'title': 'Article 2', 'publish_time': '2025.01.22', 'index': 1},
            {'title': 'Article 3', 'publish_time': '2025.01.21', 'index': 2}
        ]
        
        result = self.scraper._sort_articles_by_date(articles)
        
        self.assertEqual(result[0]['title'], 'Article 2')
        self.assertEqual(result[1]['title'], 'Article 3')
        self.assertEqual(result[2]['title'], 'Article 1')
    
    def test_sort_articles_by_index(self):
        """测试按索引排序文章（无日期时）"""
        articles = [
            {'title': 'Article 1', 'index': 2},
            {'title': 'Article 2', 'index': 0},
            {'title': 'Article 3', 'index': 1}
        ]
        
        result = self.scraper._sort_articles_by_date(articles)
        
        self.assertEqual(result[0]['title'], 'Article 1')
        self.assertEqual(result[1]['title'], 'Article 3')
        self.assertEqual(result[2]['title'], 'Article 2')
    
    @patch('requests.Session.get')
    def test_get_article_content_enhanced_success(self, mock_get):
        """测试增强获取文章内容成功"""
        mock_response = MagicMock()
        mock_response.content = '''
        <html>
            <body>
                <article>
                    <h1>Test Article</h1>
                    <p>This is the main content of the article. It should be long enough to pass the minimum length requirement.</p>
                    <p>Here is more content to make sure we have enough characters for testing purposes.</p>
                </article>
            </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.scraper.get_article_content_enhanced('https://example.com/article')
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 50)
    
    @patch('requests.Session.get')
    def test_get_article_content_enhanced_failure(self, mock_get):
        """测试增强获取文章内容失败"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection Error")
        
        result = self.scraper.get_article_content_enhanced('https://example.com/article')
        
        self.assertIsNone(result)
    
    def test_extract_content_with_strategies(self):
        """测试使用策略提取内容"""
        html_content = '''
        <html>
            <body>
                <article>
                    <h1>Test Article</h1>
                    <p>This is the main content of the article. It should be long enough to pass the minimum length requirement.</p>
                    <p>Here is more content to make sure we have enough characters for testing purposes.</p>
                </article>
                <div class="ads">This should be removed</div>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = self.scraper._extract_content_with_strategies(soup)
        
        self.assertIsNotNone(result)
        self.assertNotIn('This should be removed', result)
        self.assertIn('Test Article', result)
    
    def test_extract_with_intelligent_filtering(self):
        """测试智能过滤提取"""
        html_content = '''
        <html>
            <body>
                <h1>Test Article</h1>
                <p>Lookonchain / 2025.01.22</p>
                <p>This is the main content. X 关注Telegram 加入</p>
                <p>Follow us on Twitter Join our community</p>
                <p>Here is the actual important content about blockchain and cryptocurrency.</p>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = self.scraper._extract_with_intelligent_filtering(soup)
        
        self.assertIsNotNone(result)
        self.assertNotIn('Lookonchain', result)
        self.assertNotIn('X 关注Telegram', result)
        self.assertNotIn('Follow us on Twitter', result)
        self.assertIn('blockchain', result)
    
    def test_scrape_latest_articles_success(self):
        """测试爬取最新文章成功"""
        with patch.object(self.scraper, 'get_latest_articles_page') as mock_get_page:
            with patch.object(self.scraper, 'get_article_content_enhanced') as mock_get_content:
                
                # Mock页面获取
                html_content = '''
                <html>
                    <div id="index_feeds_list">
                        <a href="/articles/test1">Test Article 1</a>
                        <a href="/articles/test2">Test Article 2</a>
                    </div>
                </html>
                '''
                mock_get_page.return_value = BeautifulSoup(html_content, 'html.parser')
                
                # Mock内容获取
                mock_get_content.return_value = "This is the article content. " * 20  # 足够长的内容
                
                result = self.scraper.scrape_latest_articles()
                
                self.assertEqual(len(result), 2)
                self.assertEqual(result[0]['title'], 'Test Article 1')
                self.assertEqual(result[1]['title'], 'Test Article 2')
                self.assertEqual(result[0]['content'], mock_get_content.return_value)
                self.assertEqual(result[1]['content'], mock_get_content.return_value)
    
    def test_scrape_latest_articles_no_articles(self):
        """测试爬取最新文章无结果"""
        with patch.object(self.scraper, 'get_latest_articles_page') as mock_get_page:
            mock_get_page.return_value = BeautifulSoup('<html><body>No articles</body></html>', 'html.parser')
            
            result = self.scraper.scrape_latest_articles()
            
            self.assertEqual(len(result), 0)
    
    def test_analyze_page_structure(self):
        """测试分析页面结构"""
        html_content = '''
        <html>
            <body>
                <a href="/articles/test1">Article 1</a>
                <a href="/article/test2">Article 2</a>
                <a href="/other/page">Other Link</a>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 这个方法不应该抛出异常
        self.scraper._analyze_page_structure(soup)
    
    def test_cache_timeout(self):
        """测试缓存超时"""
        import time
        from datetime import datetime, timedelta
        
        cache_key = "test_key"
        mock_response = MagicMock()
        
        # 设置缓存
        self.scraper._cache_response(cache_key, mock_response)
        
        # 验证缓存有效
        self.assertTrue(self.scraper._is_cache_valid(cache_key))
        
        # 手动设置缓存时间为超时
        old_time = datetime.now() - timedelta(seconds=400)
        self.scraper.cache[cache_key] = (old_time, mock_response)
        
        # 验证缓存失效
        self.assertFalse(self.scraper._is_cache_valid(cache_key))


if __name__ == '__main__':
    unittest.main()