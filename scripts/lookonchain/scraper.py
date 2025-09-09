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
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', '.ads', '.advertisement', '.sidebar', '.menu', '.navigation']):
                    element.decompose()
                
                # 首先尝试针对 LookOnChain 的精确内容提取
                content = self._extract_lookonchain_content(soup)
                
                # 如果精确提取失败，使用通用方法
                if not content or len(content) < ARTICLE_MIN_LENGTH:
                    content = self._extract_content_fallback(soup)
                
                # 内容长度检查
                if len(content) < ARTICLE_MIN_LENGTH:
                    print(f"⚠️ 文章内容过短: {len(content)} 字符")
                    return None
                
                if len(content) > ARTICLE_MAX_LENGTH:
                    content = content[:ARTICLE_MAX_LENGTH] + "..."
                    print(f"📝 文章内容已截断至 {ARTICLE_MAX_LENGTH} 字符")
                
                # 最终内容质量检查
                quality_score = self._calculate_content_quality(content)
                if quality_score < 0.3:
                    print(f"⚠️ 内容质量过低 (评分: {quality_score:.2f})，可能包含过多无关内容")
                    return None
                
                print(f"✅ 成功获取文章内容: {len(content)} 字符，质量评分: {quality_score:.2f}")
                return content
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 获取文章失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    print(f"❌ 无法获取文章: {article_url}")
                    return None
    
    def _extract_lookonchain_content(self, soup: BeautifulSoup) -> str:
        """针对 LookOnChain 网站的精确内容提取"""
        # LookOnChain 特定的内容选择器
        lookonchain_selectors = [
            '.article-content',
            '.post-content', 
            '.entry-content',
            '.content-body',
            '[class*="article-body"]',
            '[class*="post-body"]',
            'main article',
            '.main-content article',
            '#article-content',
            '#post-content'
        ]
        
        for selector in lookonchain_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除内容区域内的无用元素
                for elem in content_elem.select('.ads, .share-buttons, .social-share, .related-posts, .comments'):
                    elem.decompose()
                
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) >= ARTICLE_MIN_LENGTH:
                    print(f"🎯 使用 LookOnChain 专用选择器: {selector}")
                    return content
        
        return ""
    
    def _extract_content_fallback(self, soup: BeautifulSoup) -> str:
        """备用内容提取方法"""
        # 尝试通用的内容选择器
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
                if len(content) >= ARTICLE_MIN_LENGTH:
                    break
        
        # 如果仍然没有找到足够内容，使用智能过滤
        if not content or len(content) < ARTICLE_MIN_LENGTH:
            content = self._extract_with_intelligent_filtering(soup)
        
        return content
    
    def _extract_with_intelligent_filtering(self, soup: BeautifulSoup) -> str:
        """使用智能过滤提取内容"""
        body = soup.find('body')
        if not body:
            return ""
        
        raw_content = body.get_text(separator=' ', strip=True)
        
        # 智能过滤模式 - 更精确地移除无关内容
        import re
        
        # 移除 LookOnChain 特有的无用文本模式
        noise_patterns = [
            r'Lookonchain\s*/\s*\d{4}\.\d{2}\.\d{2}',
            r'X\s+关注Telegram\s+加入',
            r'\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'Follow\s+us\s+on\s+(Twitter|Telegram|X)',
            r'Join\s+our\s+(community|channel|group)',
            r'Subscribe\s+to\s+our\s+(newsletter|channel)',
            r'Click\s+here\s+to\s+read\s+more',
            r'Read\s+more\s+at\s+the\s+source',
            r'Continue\s+reading',
            r'Source\s+link',
            r'Original\s+article',
            r'\b(Home|Login|Register|About|Contact|Menu|Navigation|Footer|Header|Search|Subscribe|Follow|Share|Like|Reply|Retweet|Tweet|Copy link|Download|Upload|Settings|Profile|Dashboard|Notifications|APP|应用商店|登录|注册|配置文件|安全|注销|动态|文章|搜索历史|清除全部|趋势搜索|关注我们|加入|下载图片|复制链接|相关内容|原文|热点新闻|更多热门文章|更多)\b',
            r'\b(trending|popular|latest|hot|new|more|read more|continue reading|click here|learn more|show more|load more|view all|see all)\b'
        ]
        
        filtered_content = raw_content
        for pattern in noise_patterns:
            filtered_content = re.sub(pattern, ' ', filtered_content, flags=re.IGNORECASE)
        
        # 移除多余的空白字符
        filtered_content = ' '.join(filtered_content.split())
        
        return filtered_content
    
    def _calculate_content_quality(self, content: str) -> float:
        """计算内容质量评分 (0-1)"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # 1. 长度评分 (0-0.3)
        length_score = min(len(content) / 2000, 1.0) * 0.3
        score += length_score
        
        # 2. 密度评分 - 检查是否包含足够的关键词 (0-0.3)
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'blockchain', 
            'defi', 'nft', 'token', 'coin', 'wallet', 'address', 'transaction',
            'exchange', 'trading', 'investment', 'market', 'price', 'usd',
            '美元', '比特币', '以太坊', '加密', '区块链', '代币', '交易', '投资'
        ]
        
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in crypto_keywords if keyword in content_lower)
        density_score = min(keyword_count / 10, 1.0) * 0.3
        score += density_score
        
        # 3. 结构评分 - 检查段落结构 (0-0.2)
        sentences = content.split('.')
        if len(sentences) > 3:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if 10 <= avg_sentence_length <= 30:
                score += 0.2
            elif 5 <= avg_sentence_length <= 50:
                score += 0.1
        
        # 4. 可读性评分 - 检查无意义字符比例 (0-0.2)
        meaningful_chars = sum(1 for c in content if c.isalnum() or c.isspace() or c in '.,;:!?-')
        readability_score = (meaningful_chars / len(content)) * 0.2
        score += readability_score
        
        return min(score, 1.0)
    
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