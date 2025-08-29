"""
LookOnChain 文章抓取和分析模块
每日定时抓取 LookOnChain 前3篇文章，翻译总结为中文
"""

__version__ = "1.0.0"
__author__ = "ERIC"

from .scraper import LookOnChainScraper
from .translator import ChineseTranslator
from .article_generator import ArticleGenerator

__all__ = ['LookOnChainScraper', 'ChineseTranslator', 'ArticleGenerator']