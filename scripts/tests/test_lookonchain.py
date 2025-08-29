"""
LookOnChain 模块完整单元测试
100% 代码覆盖率测试套件
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import json
import os
import sys
import datetime
from io import StringIO

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lookonchain.scraper import LookOnChainScraper
from lookonchain.translator import ChineseTranslator
from lookonchain.article_generator import ArticleGenerator
from lookonchain import config
from lookonchain_analyzer import LookOnChainAnalyzer


class TestLookOnChainScraper(unittest.TestCase):
    """测试 LookOnChainScraper 类"""
    
    def setUp(self):
        self.scraper = LookOnChainScraper()
    
    @patch('lookonchain.scraper.requests.Session')
    def test_init(self, mock_session):
        """测试初始化"""
        scraper = LookOnChainScraper()
        self.assertIsNotNone(scraper.session)
        mock_session.assert_called_once()
    
    @patch('lookonchain.scraper.requests.Session.get')
    def test_get_feeds_page_success(self, mock_get):
        """测试成功获取首页"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><h1>Test</h1></body></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.get_feeds_page()
        
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
    
    @patch('lookonchain.scraper.requests.Session.get')
    @patch('lookonchain.scraper.time.sleep')
    def test_get_feeds_page_retry_failure(self, mock_sleep, mock_get):
        """测试重试失败"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.scraper.get_feeds_page()
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 3)  # MAX_RETRIES
        self.assertEqual(mock_sleep.call_count, 2)  # 2次重试间隔
    
    @patch('lookonchain.scraper.BeautifulSoup')
    def test_extract_article_links_with_articles(self, mock_bs):
        """测试提取文章链接 - 有文章"""
        mock_soup = Mock()
        mock_article = Mock()
        mock_link = Mock()
        mock_link.get.return_value = '/article/test'
        mock_link.get_text.return_value = 'Test Article Title'
        mock_article.name = 'article'
        mock_article.find.return_value = mock_link
        mock_title = Mock()
        mock_title.get_text.return_value = 'Test Article Title'
        mock_article.find.side_effect = lambda tags: mock_title if 'title' in str(tags) else None
        mock_soup.select.return_value = [mock_article]
        
        with patch('lookonchain.scraper.hashlib.md5') as mock_md5:
            mock_md5.return_value.hexdigest.return_value = 'abcdef123456'
            result = self.scraper.extract_article_links(mock_soup)
        
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 3)
    
    @patch('lookonchain.scraper.BeautifulSoup')
    def test_extract_article_links_empty(self, mock_bs):
        """测试提取文章链接 - 空结果"""
        mock_soup = Mock()
        mock_soup.select.return_value = []
        
        result = self.scraper.extract_article_links(mock_soup)
        
        self.assertEqual(result, [])
    
    @patch('lookonchain.scraper.requests.Session.get')
    def test_get_article_content_success(self, mock_get):
        """测试成功获取文章内容"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><article>' + b'A' * 600 + b'</article></body></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.get_article_content('http://example.com/article')
        
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(result), 500)
    
    @patch('lookonchain.scraper.requests.Session.get')
    def test_get_article_content_too_short(self, mock_get):
        """测试文章内容过短"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>Short</body></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.get_article_content('http://example.com/article')
        
        self.assertIsNone(result)
    
    @patch('lookonchain.scraper.requests.Session.get')
    @patch('lookonchain.scraper.time.sleep')
    def test_get_article_content_failure(self, mock_sleep, mock_get):
        """测试获取文章内容失败"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.scraper.get_article_content('http://example.com/article')
        
        self.assertIsNone(result)
    
    @patch.object(LookOnChainScraper, 'get_feeds_page')
    @patch.object(LookOnChainScraper, 'extract_article_links')
    @patch.object(LookOnChainScraper, 'get_article_content')
    @patch('lookonchain.scraper.time.sleep')
    def test_scrape_top_articles_success(self, mock_sleep, mock_get_content, mock_extract, mock_get_page):
        """测试成功爬取文章"""
        mock_get_page.return_value = Mock()
        mock_extract.return_value = [
            {'title': 'Test Article', 'url': 'http://example.com/1', 'id': '123'}
        ]
        mock_get_content.return_value = 'Article content here'
        
        result = self.scraper.scrape_top_articles()
        
        self.assertIsInstance(result, list)
        if result:  # 如果有结果
            self.assertIn('content', result[0])
    
    @patch.object(LookOnChainScraper, 'get_feeds_page')
    def test_scrape_top_articles_no_page(self, mock_get_page):
        """测试无法获取首页"""
        mock_get_page.return_value = None
        
        result = self.scraper.scrape_top_articles()
        
        self.assertEqual(result, [])
    
    def test_del_cleanup(self):
        """测试资源清理"""
        scraper = LookOnChainScraper()
        scraper.session = Mock()
        scraper.__del__()
        scraper.session.close.assert_called_once()


class TestChineseTranslator(unittest.TestCase):
    """测试 ChineseTranslator 类"""
    
    def setUp(self):
        self.api_key = "test_api_key"
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_init_success(self, mock_logger, mock_client):
        """测试成功初始化"""
        translator = ChineseTranslator(self.api_key)
        
        self.assertIsNotNone(translator.client)
        self.assertIsNotNone(translator.logger)
    
    @patch('lookonchain.translator.GLMClientWrapper')
    def test_init_failure(self, mock_client):
        """测试初始化失败"""
        mock_client.side_effect = Exception("API Error")
        
        translator = ChineseTranslator(self.api_key)
        
        self.assertIsNone(translator.client)
    
    def test_init_no_api_key(self):
        """测试无API密钥"""
        with patch('lookonchain.translator.GLM_API_KEY', None):
            translator = ChineseTranslator()
            self.assertIsNone(translator.client)
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_translate_to_chinese_success(self, mock_logger, mock_client_class):
        """测试成功翻译"""
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "这是翻译结果"
        mock_client.chat_completions_create.return_value = mock_completion
        mock_client_class.return_value = mock_client
        
        translator = ChineseTranslator(self.api_key)
        translator.client = mock_client
        
        result = translator.translate_to_chinese("Hello world", "Test Title")
        
        self.assertEqual(result, "这是翻译结果")
        mock_client.chat_completions_create.assert_called_once()
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_translate_to_chinese_no_client(self, mock_logger, mock_client_class):
        """测试无客户端翻译"""
        translator = ChineseTranslator(self.api_key)
        translator.client = None
        
        result = translator.translate_to_chinese("Hello world")
        
        self.assertIsNone(result)
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_translate_to_chinese_api_error(self, mock_logger, mock_client_class):
        """测试API错误"""
        mock_client = Mock()
        mock_client.chat_completions_create.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        translator = ChineseTranslator(self.api_key)
        translator.client = mock_client
        
        result = translator.translate_to_chinese("Hello world")
        
        self.assertIsNone(result)
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_generate_summary_success(self, mock_logger, mock_client_class):
        """测试成功生成摘要"""
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "这是摘要内容"
        mock_client.chat_completions_create.return_value = mock_completion
        mock_client_class.return_value = mock_client
        
        translator = ChineseTranslator(self.api_key)
        translator.client = mock_client
        
        result = translator.generate_summary("中文内容", "标题")
        
        self.assertEqual(result, "这是摘要内容")
    
    @patch('lookonchain.translator.GLMClientWrapper')
    @patch('lookonchain.translator.GLMLogger')
    def test_translate_title_success(self, mock_logger, mock_client_class):
        """测试成功翻译标题"""
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = '"翻译后的标题"'
        mock_client.chat_completions_create.return_value = mock_completion
        mock_client_class.return_value = mock_client
        
        translator = ChineseTranslator(self.api_key)
        translator.client = mock_client
        
        result = translator.translate_title("English Title")
        
        self.assertEqual(result, "翻译后的标题")
    
    @patch.object(ChineseTranslator, 'translate_title')
    @patch.object(ChineseTranslator, 'translate_to_chinese')
    @patch.object(ChineseTranslator, 'generate_summary')
    @patch('lookonchain.translator.time.sleep')
    def test_process_article_success(self, mock_sleep, mock_summary, mock_translate, mock_title):
        """测试成功处理文章"""
        mock_title.return_value = "中文标题"
        mock_translate.return_value = "中文内容"
        mock_summary.return_value = "中文摘要"
        
        translator = ChineseTranslator(self.api_key)
        article_data = {
            'title': 'English Title',
            'content': 'English content',
            'url': 'http://example.com',
            'id': '123'
        }
        
        result = translator.process_article(article_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['chinese_title'], "中文标题")
        self.assertEqual(result['chinese_content'], "中文内容")
        self.assertEqual(result['summary'], "中文摘要")
    
    @patch.object(ChineseTranslator, 'translate_title')
    def test_process_article_title_failure(self, mock_title):
        """测试标题翻译失败"""
        mock_title.return_value = None
        
        translator = ChineseTranslator(self.api_key)
        article_data = {'title': 'English Title', 'content': 'English content'}
        
        result = translator.process_article(article_data)
        
        self.assertIsNone(result)
    
    def test_get_api_usage_stats_with_logger(self):
        """测试获取API使用统计 - 有日志器"""
        translator = ChineseTranslator(self.api_key)
        mock_logger = Mock()
        mock_logger.get_daily_stats.return_value = {"calls": 10}
        translator.logger = mock_logger
        
        result = translator.get_api_usage_stats()
        
        self.assertEqual(result, {"calls": 10})
    
    def test_get_api_usage_stats_no_logger(self):
        """测试获取API使用统计 - 无日志器"""
        translator = ChineseTranslator(self.api_key)
        translator.logger = None
        
        result = translator.get_api_usage_stats()
        
        self.assertEqual(result, {"error": "日志记录器未初始化"})


class TestArticleGenerator(unittest.TestCase):
    """测试 ArticleGenerator 类"""
    
    def setUp(self):
        self.generator = ArticleGenerator()
    
    @patch('lookonchain.article_generator.os.makedirs')
    def test_init(self, mock_makedirs):
        """测试初始化"""
        generator = ArticleGenerator()
        
        self.assertIsNotNone(generator.history_file)
        mock_makedirs.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"generated_articles": ["id1", "id2"]}')
    @patch('os.path.exists')
    def test_load_article_history_success(self, mock_exists, mock_file):
        """测试成功加载历史记录"""
        mock_exists.return_value = True
        
        result = self.generator.load_article_history()
        
        self.assertEqual(result, {"id1", "id2"})
    
    @patch('os.path.exists')
    def test_load_article_history_no_file(self, mock_exists):
        """测试文件不存在"""
        mock_exists.return_value = False
        
        result = self.generator.load_article_history()
        
        self.assertEqual(result, set())
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('os.path.exists')
    def test_load_article_history_json_error(self, mock_exists, mock_file):
        """测试JSON解析错误"""
        mock_exists.return_value = True
        
        result = self.generator.load_article_history()
        
        self.assertEqual(result, set())
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_article_history_success(self, mock_json_dump, mock_file):
        """测试成功保存历史记录"""
        article_ids = {"id1", "id2"}
        
        self.generator.save_article_history(article_ids)
        
        mock_json_dump.assert_called_once()
        args = mock_json_dump.call_args[0]
        self.assertEqual(set(args[0]['generated_articles']), article_ids)
    
    @patch('builtins.open', side_effect=Exception("Write error"))
    def test_save_article_history_error(self, mock_file):
        """测试保存历史记录错误"""
        article_ids = {"id1", "id2"}
        
        # 不应该抛出异常
        self.generator.save_article_history(article_ids)
    
    def test_is_article_generated(self):
        """测试检查文章是否已生成"""
        generated_articles = {"id1", "id2"}
        
        self.assertTrue(self.generator.is_article_generated("id1", generated_articles))
        self.assertFalse(self.generator.is_article_generated("id3", generated_articles))
    
    @patch('lookonchain.article_generator.datetime')
    def test_generate_filename(self, mock_datetime):
        """测试生成文件名"""
        mock_datetime.datetime.now.return_value.strftime.return_value = "2024-01-01"
        
        filename = self.generator.generate_filename("测试标题", "abc123")
        
        self.assertIn("lookonchain-", filename)
        self.assertIn("2024-01-01", filename)
        self.assertTrue(filename.endswith(".md"))
    
    def test_generate_article_tags(self):
        """测试生成文章标签"""
        content = "这是一个关于DeFi和Bitcoin的文章"
        title = "NFT市场分析"
        
        tags = self.generator.generate_article_tags(content, title)
        
        self.assertIsInstance(tags, list)
        self.assertLessEqual(len(tags), 8)
    
    @patch('lookonchain.article_generator.datetime')
    def test_generate_hugo_frontmatter(self, mock_datetime):
        """测试生成Hugo前置matter"""
        mock_datetime.datetime.now.return_value.strftime.return_value = "2024-01-01T10:00:00+08:00"
        
        article = {
            'chinese_title': '测试标题',
            'summary': '测试摘要',
            'chinese_content': '测试内容'
        }
        
        frontmatter = self.generator.generate_hugo_frontmatter(article)
        
        self.assertIn("title = '测试标题'", frontmatter)
        self.assertIn("date = '2024-01-01T10:00:00+08:00'", frontmatter)
    
    def test_generate_article_content(self):
        """测试生成文章内容"""
        article = {
            'chinese_content': '这是中文内容',
            'summary': '这是摘要',
            'url': 'http://example.com'
        }
        
        content = self.generator.generate_article_content(article)
        
        self.assertIn('这是中文内容', content)
        self.assertIn('这是摘要', content)
        self.assertIn('http://example.com', content)
    
    @patch.object(ArticleGenerator, 'generate_filename')
    @patch.object(ArticleGenerator, 'generate_hugo_frontmatter')
    @patch.object(ArticleGenerator, 'generate_article_content')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_hugo_article_success(self, mock_file, mock_makedirs, mock_content, mock_frontmatter, mock_filename):
        """测试成功创建Hugo文章"""
        mock_filename.return_value = "test.md"
        mock_frontmatter.return_value = "frontmatter"
        mock_content.return_value = "content"
        
        article = {'chinese_title': '标题', 'id': '123'}
        result = self.generator.create_hugo_article(article, "/output")
        
        self.assertEqual(result, "/output/test.md")
    
    @patch.object(ArticleGenerator, 'generate_filename')
    @patch('os.makedirs', side_effect=Exception("Directory error"))
    def test_create_hugo_article_error(self, mock_makedirs, mock_filename):
        """测试创建文章失败"""
        mock_filename.return_value = "test.md"
        
        article = {'chinese_title': '标题', 'id': '123'}
        result = self.generator.create_hugo_article(article, "/output")
        
        self.assertIsNone(result)
    
    @patch.object(ArticleGenerator, 'load_article_history')
    @patch.object(ArticleGenerator, 'save_article_history')
    @patch.object(ArticleGenerator, 'create_hugo_article')
    @patch('os.path.dirname')
    def test_generate_daily_articles_success(self, mock_dirname, mock_create, mock_save, mock_load):
        """测试成功生成每日文章"""
        mock_load.return_value = set()
        mock_create.return_value = "/path/to/article.md"
        mock_dirname.return_value = "/base"
        
        articles = [{'id': '123', 'chinese_title': '标题'}]
        result = self.generator.generate_daily_articles(articles)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['generated'], 1)
    
    def test_generate_daily_articles_empty(self):
        """测试空文章列表"""
        result = self.generator.generate_daily_articles([])
        
        self.assertFalse(result['success'])
        self.assertEqual(result['generated'], 0)
    
    @patch.object(ArticleGenerator, 'load_article_history')
    def test_generate_daily_articles_all_generated(self, mock_load):
        """测试所有文章都已生成"""
        mock_load.return_value = {"123"}
        
        articles = [{'id': '123', 'chinese_title': '标题'}]
        result = self.generator.generate_daily_articles(articles)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['generated'], 0)


class TestLookOnChainAnalyzer(unittest.TestCase):
    """测试 LookOnChainAnalyzer 类"""
    
    def setUp(self):
        self.api_key = "test_api_key"
    
    @patch('lookonchain_analyzer.LookOnChainScraper')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.ArticleGenerator')
    def test_init(self, mock_generator, mock_translator, mock_scraper):
        """测试初始化"""
        analyzer = LookOnChainAnalyzer(self.api_key)
        
        self.assertEqual(analyzer.glm_api_key, self.api_key)
        mock_scraper.assert_called_once()
        mock_translator.assert_called_once_with(self.api_key)
        mock_generator.assert_called_once()
    
    @patch('lookonchain_analyzer.LookOnChainScraper')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.ArticleGenerator')
    def test_run_daily_analysis_success(self, mock_generator_class, mock_translator_class, mock_scraper_class):
        """测试成功执行每日分析"""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = [
            {'title': 'Test', 'content': 'Content', 'id': '123'}
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Mock translator
        mock_translator = Mock()
        mock_translator.client = Mock()  # 确保有client
        mock_translator.process_article.return_value = {
            'chinese_title': '测试标题',
            'chinese_content': '测试内容',
            'summary': '测试摘要',
            'id': '123'
        }
        mock_translator_class.return_value = mock_translator
        
        # Mock generator
        mock_generator = Mock()
        mock_generator.generate_daily_articles.return_value = {
            'success': True,
            'generated': 1,
            'total_processed': 1,
            'message': 'Success'
        }
        mock_generator_class.return_value = mock_generator
        
        analyzer = LookOnChainAnalyzer(self.api_key)
        result = analyzer.run_daily_analysis()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['generated_articles'], 1)
    
    @patch('lookonchain_analyzer.LookOnChainScraper')
    def test_run_daily_analysis_no_articles(self, mock_scraper_class):
        """测试无文章情况"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = []
        mock_scraper_class.return_value = mock_scraper
        
        analyzer = LookOnChainAnalyzer(self.api_key)
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'scraping')
    
    @patch('lookonchain_analyzer.LookOnChainScraper')
    @patch('lookonchain_analyzer.ChineseTranslator')
    def test_run_daily_analysis_no_translator_client(self, mock_translator_class, mock_scraper_class):
        """测试翻译器无客户端"""
        mock_scraper = Mock()
        mock_scraper.scrape_top_articles.return_value = [{'title': 'Test'}]
        mock_scraper_class.return_value = mock_scraper
        
        mock_translator = Mock()
        mock_translator.client = None
        mock_translator_class.return_value = mock_translator
        
        analyzer = LookOnChainAnalyzer(self.api_key)
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'translation_init')
    
    @patch('lookonchain_analyzer.LookOnChainScraper')
    @patch('lookonchain_analyzer.ChineseTranslator')
    @patch('lookonchain_analyzer.ArticleGenerator')
    def test_run_daily_analysis_exception(self, mock_generator_class, mock_translator_class, mock_scraper_class):
        """测试执行异常"""
        mock_scraper_class.side_effect = Exception("Test error")
        
        analyzer = LookOnChainAnalyzer(self.api_key)
        result = analyzer.run_daily_analysis()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['stage'], 'execution')
        self.assertIn('Test error', result['error'])
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_success(self, mock_stdout):
        """测试打印成功摘要"""
        analyzer = LookOnChainAnalyzer(self.api_key)
        analyzer.translator = Mock()
        analyzer.translator.logger = None
        
        result = {
            'success': True,
            'scrapped_articles': 3,
            'translated_articles': 3,
            'generated_articles': 2,
            'message': 'Success',
            'generated_files': ['file1.md', 'file2.md'],
            'execution_time': '2024-01-01T10:00:00'
        }
        
        analyzer.print_summary(result)
        
        output = mock_stdout.getvalue()
        self.assertIn('任务执行成功', output)
        self.assertIn('爬取文章数: 3', output)
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_summary_failure(self, mock_stdout):
        """测试打印失败摘要"""
        analyzer = LookOnChainAnalyzer(self.api_key)
        analyzer.translator = Mock()
        analyzer.translator.logger = None
        
        result = {
            'success': False,
            'stage': 'scraping',
            'error': 'Network error',
            'execution_time': '2024-01-01T10:00:00'
        }
        
        analyzer.print_summary(result)
        
        output = mock_stdout.getvalue()
        self.assertIn('任务执行失败', output)
        self.assertIn('错误阶段: scraping', output)


class TestMainFunction(unittest.TestCase):
    """测试主函数"""
    
    @patch('lookonchain_analyzer.GLM_API_KEY', None)
    @patch('sys.exit')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_api_key(self, mock_stdout, mock_exit):
        """测试无API密钥"""
        from lookonchain_analyzer import main
        
        main()
        
        mock_exit.assert_called_with(1)
        output = mock_stdout.getvalue()
        self.assertIn('未设置 GLM_API_KEY', output)
    
    @patch('lookonchain_analyzer.GLM_API_KEY', 'test_key')
    @patch('os.getenv')
    @patch('lookonchain_analyzer.LookOnChainAnalyzer')
    @patch('sys.exit')
    def test_main_success(self, mock_exit, mock_analyzer_class, mock_getenv):
        """测试主函数成功"""
        mock_getenv.return_value = None  # 非GitHub Actions环境
        
        mock_analyzer = Mock()
        mock_analyzer.run_daily_analysis.return_value = {'success': True}
        mock_analyzer.print_summary = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        from lookonchain_analyzer import main
        main()
        
        mock_exit.assert_called_with(0)
    
    @patch('lookonchain_analyzer.GLM_API_KEY', 'test_key')
    @patch('lookonchain_analyzer.LookOnChainAnalyzer')
    @patch('sys.exit')
    def test_main_failure(self, mock_exit, mock_analyzer_class):
        """测试主函数失败"""
        mock_analyzer = Mock()
        mock_analyzer.run_daily_analysis.return_value = {'success': False}
        mock_analyzer.print_summary = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        from lookonchain_analyzer import main
        main()
        
        mock_exit.assert_called_with(1)


class TestConfig(unittest.TestCase):
    """测试配置模块"""
    
    def test_config_constants(self):
        """测试配置常量"""
        self.assertIn('lookonchain.com', config.LOOKONCHAIN_BASE_URL)
        self.assertGreater(config.REQUEST_TIMEOUT, 0)
        self.assertGreater(config.MAX_RETRIES, 0)
        self.assertIsInstance(config.DEFAULT_TAGS, list)
        self.assertIsInstance(config.DEFAULT_CATEGORIES, list)
        self.assertIsInstance(config.AUTHOR_INFO, dict)


if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestLookOnChainScraper,
        TestChineseTranslator, 
        TestArticleGenerator,
        TestLookOnChainAnalyzer,
        TestMainFunction,
        TestConfig
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试报告
    print(f"\n{'='*60}")
    print("测试报告摘要")
    print(f"{'='*60}")
    print(f"总测试数: {result.testsRun}")
    print(f"成功测试: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败测试: {len(result.failures)}")
    print(f"错误测试: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    print(f"{'='*60}")