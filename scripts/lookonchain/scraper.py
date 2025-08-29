"""
LookOnChain 网站爬虫模块
负责从 LookOnChain 获取前3篇文章内容
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from .config import (
    LOOKONCHAIN_FEEDS_URL, USER_AGENT, REQUEST_TIMEOUT, 
    MAX_RETRIES, RETRY_DELAY, ARTICLE_MIN_LENGTH, ARTICLE_MAX_LENGTH
)


class LookOnChainScraper:
    """LookOnChain 文章爬虫类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_feeds_page(self) -> Optional[BeautifulSoup]:
        """获取 LookOnChain 首页内容"""
        for attempt in range(MAX_RETRIES):
            try:
                print(f"🔍 正在获取 LookOnChain 首页内容... (尝试 {attempt + 1}/{MAX_RETRIES})")
                response = self.session.get(LOOKONCHAIN_FEEDS_URL, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                print("✅ 成功获取首页内容")
                return soup
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 获取首页失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print("❌ 无法获取 LookOnChain 首页")
                    return None
    
    def extract_article_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """从首页提取文章链接和基本信息"""
        articles = []
        
        try:
            # 根据 LookOnChain 网站结构提取文章
            # 这里需要分析网站的实际DOM结构来确定选择器
            article_selectors = [
                'article',  # 标准文章标签
                '.post', '.article', '.news-item',  # 常见的文章class
                '[class*="feed"], [class*="item"], [class*="post"]'  # 包含相关关键词的class
            ]
            
            for selector in article_selectors:
                article_elements = soup.select(selector)
                if article_elements:
                    print(f"📰 找到 {len(article_elements)} 个文章元素 (选择器: {selector})")
                    break
            else:
                # 如果没有找到标准结构，尝试查找包含链接的元素
                article_elements = soup.select('a[href*="article"], a[href*="post"], a[href*="news"]')
                if not article_elements:
                    # 最后尝试：查找所有包含文本内容的链接
                    article_elements = soup.select('a[href]')
                    article_elements = [elem for elem in article_elements if elem.get_text().strip()][:10]
            
            for element in article_elements[:5]:  # 只处理前5个元素，确保有足够候选
                try:
                    # 提取链接
                    link_elem = element if element.name == 'a' else element.find('a')
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href')
                    if not href:
                        continue
                    
                    # 确保是完整URL
                    full_url = urljoin(LOOKONCHAIN_FEEDS_URL, href)
                    
                    # 提取标题
                    title = ''
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]'])
                    if title_elem:
                        title = title_elem.get_text().strip()
                    else:
                        title = link_elem.get_text().strip()
                    
                    # 提取摘要
                    summary = ''
                    summary_elem = element.find(['.summary', '.excerpt', '.description', 'p'])
                    if summary_elem:
                        summary = summary_elem.get_text().strip()[:200]
                    
                    if title and len(title) > 10:  # 确保标题有意义
                        article_info = {
                            'title': title,
                            'url': full_url,
                            'summary': summary,
                            'id': hashlib.md5(full_url.encode()).hexdigest()[:12]
                        }
                        articles.append(article_info)
                        
                except Exception as e:
                    print(f"⚠️ 解析文章元素失败: {e}")
                    continue
            
            print(f"📋 成功提取 {len(articles)} 个文章链接")
            return articles[:3]  # 只返回前3篇
            
        except Exception as e:
            print(f"❌ 提取文章链接失败: {e}")
            return []
    
    def get_article_content(self, article_url: str) -> Optional[str]:
        """获取单篇文章的详细内容"""
        for attempt in range(MAX_RETRIES):
            try:
                print(f"📖 正在获取文章内容: {article_url}")
                response = self.session.get(article_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 移除不需要的元素
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', '.ads', '.advertisement']):
                    element.decompose()
                
                # 尝试多种方式提取文章主体内容
                content_selectors = [
                    'article', '.article-content', '.post-content', '.content',
                    '.main-content', '[class*="content"]', '.entry-content',
                    'main', '[role="main"]'
                ]
                
                content = ''
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content = content_elem.get_text(separator=' ', strip=True)
                        break
                
                # 如果没有找到主要内容区域，提取body中的文本
                if not content or len(content) < ARTICLE_MIN_LENGTH:
                    body = soup.find('body')
                    if body:
                        content = body.get_text(separator=' ', strip=True)
                
                # 内容长度检查
                if len(content) < ARTICLE_MIN_LENGTH:
                    print(f"⚠️ 文章内容过短: {len(content)} 字符")
                    return None
                
                if len(content) > ARTICLE_MAX_LENGTH:
                    content = content[:ARTICLE_MAX_LENGTH] + "..."
                    print(f"📝 文章内容已截断至 {ARTICLE_MAX_LENGTH} 字符")
                
                print(f"✅ 成功获取文章内容: {len(content)} 字符")
                return content
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 获取文章失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print(f"❌ 无法获取文章: {article_url}")
                    return None
    
    def scrape_top_articles(self) -> List[Dict[str, str]]:
        """爬取前3篇文章的完整信息"""
        print("🚀 开始爬取 LookOnChain 文章...")
        
        # 获取首页
        soup = self.get_feeds_page()
        if not soup:
            return []
        
        # 提取文章链接
        article_links = self.extract_article_links(soup)
        if not article_links:
            print("❌ 未找到任何文章链接")
            return []
        
        print(f"📚 准备获取 {len(article_links)} 篇文章的详细内容")
        
        # 获取每篇文章的详细内容
        complete_articles = []
        for i, article_info in enumerate(article_links, 1):
            print(f"\n📰 处理文章 {i}: {article_info['title'][:50]}...")
            
            content = self.get_article_content(article_info['url'])
            if content:
                article_info['content'] = content
                complete_articles.append(article_info)
                print(f"✅ 文章 {i} 处理完成")
            else:
                print(f"❌ 文章 {i} 内容获取失败")
            
            # 避免请求过快
            if i < len(article_links):
                time.sleep(1)
        
        print(f"\n🎉 成功爬取 {len(complete_articles)} 篇完整文章")
        return complete_articles
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()