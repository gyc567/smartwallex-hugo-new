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
    LOOKONCHAIN_BASE_URL, LOOKONCHAIN_FEEDS_URL, USER_AGENT, REQUEST_TIMEOUT, 
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
            # 根据实际分析的 LookOnChain 网站结构提取文章
            # 首先尝试主要的文章列表容器
            feeds_container = soup.select_one('#index_feeds_list')
            if feeds_container:
                print("📰 找到主要文章列表容器 #index_feeds_list")
                article_elements = feeds_container.select('a[href*="/articles/"]')
            else:
                # 备选方案：直接查找文章链接
                article_elements = soup.select('a[href*="/articles/"]')
            
            if article_elements:
                print(f"📰 找到 {len(article_elements)} 个文章链接")
            else:
                # 如果没有找到文章链接，尝试其他可能的选择器
                fallback_selectors = [
                    'a[href*="article"]',  # 包含article的链接
                    'a[href*="post"]',     # 包含post的链接
                    'article a',           # 在article标签内的链接
                    '.post a', '.article a', '.news-item a',  # 在常见文章class内的链接
                ]
                
                for selector in fallback_selectors:
                    article_elements = soup.select(selector)
                    if article_elements:
                        print(f"📰 通过备选方案找到 {len(article_elements)} 个文章元素 (选择器: {selector})")
                        break
                else:
                    print("⚠️ 未找到任何文章链接，将分析页面结构")
                    # 调试：输出页面的主要链接
                    all_links = soup.select('a[href]')[:10]
                    print("🔍 页面前10个链接:")
                    for i, link in enumerate(all_links, 1):
                        href = link.get('href', '')
                        text = link.get_text().strip()[:50]
                        print(f"   {i}. {href} - {text}")
                    article_elements = []
            
            for element in article_elements[:5]:  # 只处理前5个元素，确保有足够候选
                try:
                    # 确保element是链接元素
                    link_elem = element if element.name == 'a' else element.find('a')
                    if not link_elem:
                        continue
                    
                    href = link_elem.get('href')
                    if not href:
                        continue
                    
                    # 确保是完整URL
                    full_url = urljoin(LOOKONCHAIN_BASE_URL, href)
                    
                    # 提取标题 - 根据LookOnChain网站结构，标题通常在链接文本中
                    title = link_elem.get_text().strip()
                    
                    # 如果标题为空或过短，尝试其他方法
                    if not title or len(title) < 10:
                        # 尝试查找父容器中的标题元素
                        parent = link_elem.parent
                        if parent:
                            title_candidates = parent.select('.title, [class*="title"], h1, h2, h3, h4')
                            for candidate in title_candidates:
                                candidate_text = candidate.get_text().strip()
                                if candidate_text and len(candidate_text) > 10:
                                    title = candidate_text
                                    break
                    
                    # 清理标题中的日期等额外信息
                    if title:
                        # 移除日期格式如 "2025.01.22"
                        import re
                        title = re.sub(r'\d{4}\.\d{2}\.\d{2}', '', title).strip()
                        # 移除多余的空白字符
                        title = ' '.join(title.split())
                    
                    # 提取摘要 - 在LookOnChain中可能不容易获取，先设为空
                    summary = ''
                    
                    # 验证文章URL格式
                    if '/articles/' in href and title and len(title) > 10:
                        article_info = {
                            'title': title,
                            'url': full_url,
                            'summary': summary,
                            'id': hashlib.md5(full_url.encode()).hexdigest()[:12]
                        }
                        articles.append(article_info)
                        print(f"✅ 提取文章: {title[:50]}...")
                        
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
                
                # 如果没有找到主要内容区域，尝试更精确的选择器
                if not content or len(content) < ARTICLE_MIN_LENGTH:
                    # 尝试移除导航、页脚、侧边栏等元素后再提取
                    for elem in soup.select('nav, footer, aside, header, .nav, .footer, .sidebar, .menu'):
                        if elem:
                            elem.decompose()
                    
                    # 尝试更精确的内容选择器
                    precise_selectors = [
                        'main article', 'div[class*="post"]', 'div[class*="article"]',
                        '.post-body', '.article-body', '.entry', '.post'
                    ]
                    
                    for selector in precise_selectors:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            content = content_elem.get_text(separator=' ', strip=True)
                            if len(content) >= ARTICLE_MIN_LENGTH:
                                break
                    
                    # 最后尝试body，但过滤掉明显的导航文本
                    if not content or len(content) < ARTICLE_MIN_LENGTH:
                        body = soup.find('body')
                        if body:
                            raw_content = body.get_text(separator=' ', strip=True)
                            # 简单过滤：移除常见的导航文本模式
                            import re
                            # 移除菜单、导航相关文本
                            filtered_content = re.sub(r'\b(Home|Login|Register|About|Contact|Menu|Navigation|Footer|Header|Search|Subscribe|Follow|Tweet|Share|Like|Reply|Retweet)\b', '', raw_content, flags=re.IGNORECASE)
                            # 移除常见的无用词汇
                            filtered_content = re.sub(r'\b(trending|popular|latest|more|read more|continue reading|click here|learn more)\b', '', filtered_content, flags=re.IGNORECASE)
                            # 移除多余空格
                            filtered_content = ' '.join(filtered_content.split())
                            
                            if len(filtered_content) >= ARTICLE_MIN_LENGTH:
                                content = filtered_content
                
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