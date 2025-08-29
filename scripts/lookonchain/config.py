"""
LookOnChain 模块配置文件
"""

import os

# LookOnChain 网站配置
LOOKONCHAIN_BASE_URL = "https://www.lookonchain.com"
LOOKONCHAIN_FEEDS_URL = f"{LOOKONCHAIN_BASE_URL}/index.aspx"

# 用户代理和请求配置
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# GLM API 配置（复用主配置）
GLM_API_KEY = os.getenv('GLM_API_KEY')
GLM_API_BASE = 'https://open.bigmodel.cn/api/paas/v4/'
GLM_MODEL = 'glm-4.5'

# 翻译和总结配置
TRANSLATION_TEMPERATURE = 0.3  # 翻译使用较低温度保持准确性
SUMMARY_TEMPERATURE = 0.7      # 总结使用中等温度保持创造性
MAX_TOKENS_TRANSLATION = 4000  # 翻译最大token数
MAX_TOKENS_SUMMARY = 2000     # 总结最大token数

# 文章生成配置
MAX_ARTICLES_PER_DAY = 3       # 每日最多抓取文章数
ARTICLE_MIN_LENGTH = 500       # 原文最小长度（字符）
ARTICLE_MAX_LENGTH = 10000     # 原文最大长度（字符）

# 作者信息配置（复用主配置）
AUTHOR_INFO = {
    'name': 'ERIC',
    'title': '《区块链核心技术与应用》作者之一，前火币机构事业部|矿池技术主管，比特财商|Nxt Venture Capital 创始人',
    'email': 'gyc567@gmail.com',
    'twitter': '@EricBlock2100',
    'wechat': '360369487',
    'telegram': 'https://t.me/fatoshi_block',
    'telegram_channel': 'https://t.me/cryptochanneleric',
    'telegram_group': 'https://t.me/btcgogopen',
    'youtube': 'https://www.youtube.com/@0XBitFinance',
    'website': 'https://www.smartwallex.com/',
    'wechat_public': '比特财商'
}

# 文章标签和分类
DEFAULT_TAGS = ['LookOnChain', '链上数据', '加密货币分析', '智能合约', '区块链新闻']
DEFAULT_CATEGORIES = ['链上数据分析']
DEFAULT_KEYWORDS = ['LookOnChain分析', '链上数据追踪', '加密货币监控', '区块链情报']

# 数据目录配置
DATA_DIR = 'data'
LOOKONCHAIN_HISTORY_FILE = 'data/lookonchain_articles.json'