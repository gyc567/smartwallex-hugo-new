#!/usr/bin/env python3
"""
LookOnChain 增强爬虫模块
专门用于获取最新前三篇文章并进行内容处理
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from .config import (
    LOOKONCHAIN_BASE_URL, LOOKONCHAIN_FEEDS_URL, USER_AGENT, REQUEST_TIMEOUT,
    MAX_RETRIES, RETRY_DELAY, ARTICLE_MIN_LENGTH, ARTICLE_MAX_LENGTH
)


class EnhancedLookOnChainScraper:
    """增强的LookOnChain爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': LOOKONCHAIN_BASE_URL
        })
        
        # 缓存机制，避免重复请求
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        
        print("🕷️ 增强LookOnChain爬虫初始化完成")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        
        cache_time, _ = self.cache[cache_key]
        return (datetime.now() - cache_time).total_seconds() < self.cache_timeout
    
    def _get_cached_response(self, cache_key: str) -> Optional[requests.Response]:
        """获取缓存的响应"""
        if self._is_cache_valid(cache_key):
            _, response = self.cache[cache_key]
            print(f"📦 使用缓存响应: {cache_key}")
            return response
        return None
    
    def _cache_response(self, cache_key: str, response: requests.Response):
        """缓存响应"""
        self.cache[cache_key] = (datetime.now(), response)
        print(f"💾 缓存响应: {cache_key}")
    
    def get_latest_articles_page(self) -> Optional[BeautifulSoup]:
        """获取最新文章页面"""
        cache_key = "latest_articles_page"
        
        # 尝试从缓存获取
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return BeautifulSoup(cached_response.content, 'html.parser')
        
        # 没有缓存，发起请求
        for attempt in range(MAX_RETRIES):
            try:
                print(f"🔍 正在获取最新文章页面... (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(LOOKONCHAIN_FEEDS_URL, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # 缓存响应
                self._cache_response(cache_key, response)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                print("✅ 成功获取最新文章页面")
                return soup
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 获取最新文章页面失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print("❌ 无法获取最新文章页面")
                    return None
    
    def extract_latest_article_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """提取最新文章链接"""
        articles = []
        
        try:
            print("🔍 开始提取最新文章链接...")
            
            # 多种选择器策略，确保能找到文章
            selectors = [
                # 主要选择器
                ('#index_feeds_list a[href*="/articles/"]', "主要文章列表"),
                ('.article-list a[href*="/articles/"]', "文章列表"),
                ('.news-list a[href*="/articles/"]', "新闻列表"),
                ('.feed-list a[href*="/articles/"]', "Feed列表"),
                
                # 备用选择器
                ('a[href*="/articles/"]', "所有文章链接"),
                ('article a[href*="article"]', "文章标签内链接"),
                ('.post a[href*="post"]', "帖子链接"),
                ('.content a[href*="article"]', "内容区域链接"),
                
                # 更通用的选择器
                ('a[href*="article"]', "包含article的链接"),
                ('a[href*="post"]', "包含post的链接"),
                ('.article-item a', "文章项链接"),
                ('.news-item a', "新闻项链接")
            ]
            
            article_elements = []
            used_selector = None
            
            for selector, description in selectors:
                elements = soup.select(selector)
                if elements:
                    article_elements = elements[:10]  # 取前10个作为候选
                    used_selector = selector
                    print(f"📰 通过选择器找到 {len(article_elements)} 个候选文章: {description} ({selector})")
                    break
            
            if not article_elements:
                print("⚠️ 未找到任何文章链接，分析页面结构...")
                self._analyze_page_structure(soup)
                return []
            
            # 处理找到的文章元素
            for i, element in enumerate(article_elements):
                try:
                    article_info = self._parse_article_element(element, i)
                    if article_info:
                        articles.append(article_info)
                        print(f"✅ 提取文章 {i+1}: {article_info['title'][:40]}...")
                    
                except Exception as e:
                    print(f"⚠️ 解析文章元素 {i+1} 失败: {e}")
                    continue
            
            # 按时间排序（如果有的话）并取前3篇
            articles = self._sort_articles_by_date(articles)[:3]
            
            print(f"📋 成功提取 {len(articles)} 篇最新文章")
            return articles
            
        except Exception as e:
            print(f"❌ 提取文章链接失败: {e}")
            return []
    
    def _parse_article_element(self, element, index: int) -> Optional[Dict[str, str]]:
        """解析文章元素"""
        try:
            # 确保是链接元素
            link_elem = element if element.name == 'a' else element.find('a')
            if not link_elem:
                return None
            
            href = link_elem.get('href')
            if not href:
                return None
            
            # 构建完整URL
            full_url = urljoin(LOOKONCHAIN_BASE_URL, href)
            
            # 提取标题
            title = self._extract_title_from_element(link_elem, element)
            
            # 提取发布时间
            publish_time = self._extract_publish_time(element)
            
            # 验证文章URL格式
            if '/articles/' not in href and 'article' not in href.lower():
                return None
            
            if not title or len(title.strip()) < 10:
                return None
            
            # 生成文章ID
            article_id = hashlib.md5(full_url.encode()).hexdigest()[:12]
            
            article_info = {
                'title': title.strip(),
                'url': full_url,
                'publish_time': publish_time,
                'index': index,
                'id': article_id
            }
            
            return article_info
            
        except Exception as e:
            print(f"⚠️ 解析文章元素失败: {e}")
            return None
    
    def _extract_title_from_element(self, link_elem, parent_element) -> str:
        """从元素中提取标题"""
        # 首先尝试链接文本
        title = link_elem.get_text().strip()
        
        # 如果标题太短，尝试从父元素获取
        if len(title) < 10:
            # 尝试不同的标题选择器
            title_selectors = [
                '.title', '[class*="title"]', 
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '.headline', '[class*="headline"]',
                '.post-title', '.article-title'
            ]
            
            for selector in title_selectors:
                title_elem = parent_element.select_one(selector)
                if title_elem:
                    candidate_title = title_elem.get_text().strip()
                    if len(candidate_title) > 10:
                        title = candidate_title
                        break
            
            # 如果还是太短，尝试获取父元素的文本内容
            if len(title) < 10:
                parent_text = parent_element.get_text().strip()
                # 提取第一行作为标题
                lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                if lines and len(lines[0]) > 10:
                    title = lines[0]
        
        # 清理标题
        title = self._clean_title(title)
        
        return title
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        import re
        
        # 移除日期格式
        title = re.sub(r'\d{4}\.\d{2}\.\d{2}', '', title)
        title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)
        
        # 移除时间格式
        title = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?', '', title)
        
        # 移除多余的空白字符
        title = ' '.join(title.split())
        
        return title.strip()
    
    def _extract_publish_time(self, element) -> Optional[str]:
        """提取发布时间"""
        import re
        
        # 尝试找到时间元素
        time_selectors = [
            'time', '.time', '[class*="time"]', 
            '.date', '[class*="date"]',
            '.published', '[class*="published"]'
        ]
        
        for selector in time_selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                time_text = time_elem.get_text().strip()
                
                # 尝试解析时间格式
                time_patterns = [
                    r'(\d{4}\.\d{2}\.\d{2})',
                    r'(\d{4}-\d{2}-\d{2})',
                    r'(\d{2}/\d{2}/\d{4})',
                    r'(\d{2}\.\d{2}\.\d{4})'
                ]
                
                for pattern in time_patterns:
                    match = re.search(pattern, time_text)
                    if match:
                        return match.group(1)
        
        return None
    
    def _sort_articles_by_date(self, articles: List[Dict]) -> List[Dict]:
        """按日期排序文章"""
        def get_sort_key(article):
            # 优先使用发布时间，其次使用索引
            publish_time = article.get('publish_time')
            if publish_time:
                # 将各种日期格式统一为可比较的格式
                try:
                    if '.' in publish_time:
                        date_obj = datetime.strptime(publish_time, '%Y.%m.%d')
                    elif '-' in publish_time:
                        date_obj = datetime.strptime(publish_time, '%Y-%m-%d')
                    elif '/' in publish_time:
                        date_obj = datetime.strptime(publish_time, '%m/%d/%Y')
                    else:
                        date_obj = datetime.now()
                    
                    return (date_obj, article.get('index', 999))
                    
                except ValueError:
                    pass
            
            # 如果没有有效的发布时间，使用索引
            return (datetime.min, article.get('index', 999))
        
        return sorted(articles, key=get_sort_key, reverse=True)
    
    def _analyze_page_structure(self, soup: BeautifulSoup):
        """分析页面结构，用于调试"""
        print("🔍 页面结构分析:")
        
        # 查找所有包含"article"的链接
        article_links = soup.select('a[href*="article"]')
        print(f"   包含'article'的链接: {len(article_links)} 个")
        
        # 查找所有包含"/articles/"的链接
        articles_links = soup.select('a[href*="/articles/"]')
        print(f"   包含'/articles/'的链接: {len(articles_links)} 个")
        
        # 显示页面前10个链接
        all_links = soup.select('a[href]')[:10]
        print("   页面前10个链接:")
        for i, link in enumerate(all_links, 1):
            href = link.get('href', '')[:80]
            text = link.get_text().strip()[:50]
            print(f"     {i}. {href} - {text}")
    
    def get_article_content_enhanced(self, article_url: str) -> Optional[str]:
        """增强的文章内容获取"""
        cache_key = f"article_content_{hashlib.md5(article_url.encode()).hexdigest()[:8]}"
        
        # 尝试从缓存获取
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return self._extract_content_from_response(cached_response)
        
        # 没有缓存，发起请求
        for attempt in range(MAX_RETRIES):
            try:
                print(f"📖 正在获取文章内容: {article_url}")
                response = self.session.get(article_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # 缓存响应
                self._cache_response(cache_key, response)
                
                content = self._extract_content_from_response(response)
                
                if content:
                    print(f"✅ 成功获取文章内容: {len(content)} 字符")
                    return content
                else:
                    print(f"⚠️ 无法从页面提取有效内容")
                    return None
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 获取文章失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print(f"❌ 无法获取文章: {article_url}")
                    return None
    
    def _extract_content_from_response(self, response: requests.Response) -> Optional[str]:
        """从响应中提取内容"""
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                           '.ads', '.advertisement', '.sidebar', '.menu', '.navigation',
                           '.social-share', '.share-buttons', '.comments', '.related-posts']):
            element.decompose()
        
        # 尝试多种内容提取策略
        content = self._extract_content_with_strategies(soup)
        
        if not content or len(content) < ARTICLE_MIN_LENGTH:
            return None
        
        if len(content) > ARTICLE_MAX_LENGTH:
            content = content[:ARTICLE_MAX_LENGTH] + "..."
        
        return content
    
    def _extract_content_with_strategies(self, soup: BeautifulSoup) -> str:
        """使用多种策略提取内容"""
        # 策略1：专用选择器
        strategies = [
            # LookOnChain专用选择器
            ('.article-content', "文章内容"),
            ('.post-content', "帖子内容"),
            ('.entry-content', "条目内容"),
            ('.content-body', "内容主体"),
            ('#article-content', "文章内容ID"),
            ('#post-content', "帖子内容ID"),
            
            # 通用选择器
            ('article', "文章标签"),
            ('.content', "内容类"),
            ('.main-content', "主要内容"),
            ('main', "主要标签"),
            ('[role="main"]', "主要角色"),
            ('.post-body', "帖子主体"),
            ('.article-body', "文章主体")
        ]
        
        for selector, description in strategies:
            elements = soup.select(selector)
            for elem in elements:
                content = elem.get_text(separator=' ', strip=True)
                if len(content) >= ARTICLE_MIN_LENGTH:
                    print(f"🎯 使用策略 '{description}': {selector}")
                    return content
        
        # 策略2：智能过滤
        return self._extract_with_intelligent_filtering(soup)
    
    def _extract_with_intelligent_filtering(self, soup: BeautifulSoup) -> str:
        """智能过滤提取内容"""
        body = soup.find('body')
        if not body:
            return ""
        
        raw_content = body.get_text(separator=' ', strip=True)
        
        # 移除噪声
        import re
        
        noise_patterns = [
            r'Lookonchain\s*/\s*\d{4}\.\d{2}\.\d{2}',
            r'X\s+关注Telegram\s+加入',
            r'\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'Follow\s+us\s+on\s+(Twitter|Telegram|X)',
            r'Join\s+our\s+(community|channel|group)',
            r'(Home|Login|Register|About|Contact|Menu|Navigation|Footer|Header|Search|Subscribe|Follow|Share|Like|Reply|Retweet|Tweet|Copy link|Download|Upload|Settings|Profile|Dashboard|Notifications|APP|应用商店|登录|注册|配置文件|安全|注销|动态|文章|搜索历史|清除全部|趋势搜索|关注我们|加入|下载图片|复制链接|相关内容|原文|热点新闻|更多热门文章|更多)',
            r'(trending|popular|latest|hot|new|more|read more|continue reading|click here|learn more|show more|load more|view all|see all)'
        ]
        
        filtered_content = raw_content
        for pattern in noise_patterns:
            filtered_content = re.sub(pattern, ' ', filtered_content, flags=re.IGNORECASE)
        
        # 移除多余的空白字符
        filtered_content = ' '.join(filtered_content.split())
        
        return filtered_content
    
    def scrape_latest_articles(self) -> List[Dict[str, str]]:
        """爬取最新3篇文章"""
        print("🚀 开始爬取最新LookOnChain文章...")
        
        # 获取最新文章页面
        soup = self.get_latest_articles_page()
        if not soup:
            return []
        
        # 提取文章链接
        article_links = self.extract_latest_article_links(soup)
        if not article_links:
            print("❌ 未找到任何文章链接")
            return []
        
        print(f"📚 准备获取 {len(article_links)} 篇文章的详细内容")
        
        # 获取每篇文章的详细内容
        complete_articles = []
        for i, article_info in enumerate(article_links, 1):
            print(f"\n📰 获取文章 {i}: {article_info['title'][:50]}...")
            
            content = self.get_article_content_enhanced(article_info['url'])
            if content:
                article_info['content'] = content
                complete_articles.append(article_info)
                print(f"✅ 文章 {i} 获取完成")
            else:
                print(f"❌ 文章 {i} 内容获取失败")
            
            # 避免请求过快
            if i < len(article_links):
                time.sleep(1)
        
        print(f"\n🎉 成功爬取 {len(complete_articles)} 篇最新文章")
        return complete_articles
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()