"""
配置文件
"""

import os

# GitHub API配置
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # 可选，提高API限制
GITHUB_API_BASE = 'https://api.github.com'

# 搜索配置
SEARCH_KEYWORDS = [
    'cryptocurrency', 'blockchain', 'bitcoin', 'ethereum', 
    'defi', 'web3', 'crypto', 'dapp', 'smart-contract',
    'trading', 'wallet', 'exchange', 'nft', 'dao'
]

# 项目筛选条件
MIN_STARS = 100  # 最小星标数
DAYS_BACK = 7   # 搜索最近N天的项目
MAX_PROJECTS = 3  # 每日最多分析项目数

# 文章生成配置
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

# 项目分类关键词
PROJECT_CATEGORIES = {
    'DeFi协议': ['defi', 'decentralized finance', 'yield', 'liquidity', 'amm', 'dex', 'lending', 'swap'],
    '区块链基础设施': ['blockchain', 'consensus', 'validator', 'node', 'network', 'protocol', 'layer2', 'scaling'],
    '交易工具': ['trading', 'exchange', 'arbitrage', 'bot', 'strategy', 'portfolio', 'backtest'],
    '钱包应用': ['wallet', 'custody', 'keys', 'seed', 'mnemonic', 'hardware', 'multisig'],
    'NFT平台': ['nft', 'non-fungible', 'collectible', 'marketplace', 'art', 'gaming', 'metaverse'],
    '开发工具': ['sdk', 'api', 'framework', 'library', 'development', 'smart contract', 'solidity'],
    '数据分析': ['analytics', 'data', 'metrics', 'dashboard', 'monitoring', 'explorer', 'indexer'],
    '跨链桥': ['bridge', 'cross-chain', 'interoperability', 'multichain', 'relay'],
    '隐私保护': ['privacy', 'anonymous', 'zero-knowledge', 'zk', 'mixer', 'confidential'],
    '游戏应用': ['game', 'gaming', 'play-to-earn', 'gamefi', 'virtual world']
}

# Hugo文章模板配置
HUGO_FRONT_MATTER_TEMPLATE = """+++
date = '{date}'
draft = false
title = '{title}'
description = '{description}'
tags = {tags}
categories = {categories}
keywords = {keywords}
+++"""