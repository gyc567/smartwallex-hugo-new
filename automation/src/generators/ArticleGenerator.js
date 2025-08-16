import fs from 'fs-extra';
import path from 'path';
import matter from 'gray-matter';
import slugify from 'slugify';

/**
 * ArticleGenerator class for converting processed tweets into markdown articles
 * Implements requirements 2.2, 2.4, and 2.6 for Hugo-compatible article generation
 */
class ArticleGenerator {
  constructor(templatePath = 'md-template.md') {
    this.templatePath = templatePath;
    this.template = null;
  }

  /**
   * Load the markdown template file
   * @returns {Promise<void>}
   */
  async loadTemplate() {
    try {
      const templateContent = await fs.readFile(this.templatePath, 'utf-8');
      this.template = matter(templateContent);
    } catch (error) {
      throw new Error(`Failed to load template: ${error.message}`);
    }
  }

  /**
   * Generate a complete markdown article from tweet data
   * Requirement 2.2: Use existing md-template.md format as template structure
   * @param {Object} tweetData - Processed tweet data
   * @param {string} translatedContent - Chinese translation of tweet content
   * @param {string} enhancedContent - Enhanced article content with context
   * @returns {Promise<Object>} Generated article with content and metadata
   */
  async generateArticle(tweetData, translatedContent, enhancedContent) {
    if (!this.template) {
      await this.loadTemplate();
    }

    // Generate metadata for the article
    const metadata = this.generateMetadata(tweetData, translatedContent);
    
    // Apply template with the generated metadata and content
    const articleContent = this.applyTemplate(metadata, enhancedContent, tweetData);
    
    // Generate filename
    const filename = this.generateFilename(metadata.title, metadata.date);

    return {
      frontMatter: metadata,
      content: articleContent,
      filename,
      fullContent: this.formatFullArticle(metadata, articleContent)
    };
  }

  /**
   * Apply template structure with metadata and content
   * Requirement 2.4: Include proper front matter with title, date, tags, categories, and description in Chinese
   * @param {Object} metadata - Article metadata
   * @param {string} content - Article content
   * @param {Object} tweetData - Original tweet data
   * @returns {string} Formatted article content
   */
  applyTemplate(metadata, content, tweetData) {
    // Create the main article content with enhanced content and original tweet info
    const articleBody = `${content}

## 原始推文信息
- **作者**: ${tweetData.author.displayName} (@${tweetData.author.username})
- **发布时间**: ${new Date(tweetData.createdAt).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
- **转发数**: ${tweetData.metrics.retweetCount.toLocaleString()}
- **点赞数**: ${tweetData.metrics.likeCount.toLocaleString()}
- **回复数**: ${tweetData.metrics.replyCount.toLocaleString()}
- **原始链接**: [查看原推文](${tweetData.url})

## 关于作者

**ERIC** - 《区块链核心技术与应用》作者之一，前火币机构事业部|矿池技术主管，比特财商|Nxt Venture Capital 创始人

### 🔗 联系方式与平台

- **📧 邮箱**: [gyc567@gmail.com](mailto:gyc567@gmail.com)
- **🐦 Twitter**: [@EricBlock2100](https://twitter.com/EricBlock2100)
- **💬 微信**: 360369487
- **📱 Telegram**: [https://t.me/fatoshi_block](https://t.me/fatoshi_block)
- **📢 Telegram频道**: [https://t.me/cryptochanneleric](https://t.me/cryptochanneleric)
- **👥 加密情报TG群**: [https://t.me/btcgogopen](https://t.me/btcgogopen)
- **🎥 YouTube频道**: [https://www.youtube.com/@0XBitFinance](https://www.youtube.com/@0XBitFinance)

### 🌐 相关平台

- **📊 加密货币信息聚合网站**: [https://www.smartwallex.com/](https://www.smartwallex.com/)
- **📖 公众号**: 比特财商

*欢迎关注我的各个平台，获取最新的加密货币市场分析和投资洞察！*`;

    return articleBody;
  }

  /**
   * Generate metadata for tags, categories, and SEO data
   * Requirement 2.6: Include relevant cryptocurrency and blockchain tags in Chinese
   * @param {Object} tweetData - Original tweet data
   * @param {string} translatedContent - Chinese translation
   * @returns {Object} Article metadata
   */
  generateMetadata(tweetData, translatedContent) {
    // Generate Chinese title based on tweet content
    const title = this.generateChineseTitle(tweetData, translatedContent);
    
    // Generate description from translated content (first 150 characters)
    const description = translatedContent.length > 150 
      ? translatedContent.substring(0, 147) + '...'
      : translatedContent;

    // Generate cryptocurrency and blockchain tags in Chinese
    const tags = this.generateCryptoTags(tweetData.text, translatedContent);
    
    // Generate keywords for SEO
    const keywords = this.generateKeywords(tweetData.text, translatedContent, tags);

    return {
      date: new Date().toISOString().replace('T', ' ').substring(0, 19) + '+08:00',
      draft: false,
      title,
      description,
      tags,
      categories: ['推文分析'],
      keywords
    };
  }

  /**
   * Generate engaging Chinese title from tweet content
   * Requirement 2.5: Generate engaging Chinese titles that reflect tweet content
   * @param {Object} tweetData - Original tweet data
   * @param {string} translatedContent - Chinese translation
   * @returns {string} Generated Chinese title
   */
  generateChineseTitle(tweetData, translatedContent) {
    // Extract key topics from the tweet
    const text = tweetData.text.toLowerCase();
    const author = tweetData.author.displayName;
    
    // Common crypto keywords and their Chinese translations
    const cryptoKeywords = {
      'bitcoin': '比特币',
      'btc': 'BTC',
      'ethereum': '以太坊',
      'eth': 'ETH',
      'defi': 'DeFi',
      'nft': 'NFT',
      'web3': 'Web3',
      'blockchain': '区块链',
      'crypto': '加密货币',
      'altcoin': '山寨币',
      'trading': '交易',
      'market': '市场',
      'price': '价格',
      'bull': '牛市',
      'bear': '熊市'
    };

    // Find relevant keywords in the tweet
    const foundKeywords = [];
    for (const [eng, chn] of Object.entries(cryptoKeywords)) {
      if (text.includes(eng)) {
        foundKeywords.push(chn);
      }
    }

    // Generate title based on content and keywords
    let title;
    if (foundKeywords.length > 0) {
      const mainKeyword = foundKeywords[0];
      title = `${author}分享${mainKeyword}最新观点：${translatedContent.substring(0, 30)}...`;
    } else {
      title = `${author}加密货币市场分析：${translatedContent.substring(0, 40)}...`;
    }

    // Clean up title
    title = title.replace(/[<>:"/\\|?*]/g, '').trim();
    
    return title.length > 100 ? title.substring(0, 97) + '...' : title;
  }

  /**
   * Generate relevant cryptocurrency and blockchain tags in Chinese
   * @param {string} originalText - Original tweet text
   * @param {string} translatedContent - Chinese translation
   * @returns {Array<string>} Array of Chinese tags
   */
  generateCryptoTags(originalText, translatedContent) {
    const text = originalText.toLowerCase();
    const tags = new Set();

    // Base tags
    tags.add('加密货币');
    tags.add('区块链');
    tags.add('推特分析');

    // Cryptocurrency-specific tags
    const cryptoMap = {
      'bitcoin': '比特币',
      'btc': 'BTC',
      'ethereum': '以太坊',
      'eth': 'ETH',
      'defi': 'DeFi',
      'nft': 'NFT',
      'web3': 'Web3',
      'altcoin': '山寨币',
      'solana': 'Solana',
      'sol': 'SOL',
      'cardano': 'Cardano',
      'ada': 'ADA',
      'polygon': 'Polygon',
      'matic': 'MATIC',
      'chainlink': 'Chainlink',
      'link': 'LINK'
    };

    // Market-related tags
    const marketMap = {
      'trading': '交易',
      'market': '市场分析',
      'price': '价格分析',
      'bull': '牛市',
      'bear': '熊市',
      'pump': '上涨',
      'dump': '下跌',
      'hodl': 'HODL',
      'dyor': 'DYOR'
    };

    // Technical tags
    const techMap = {
      'mining': '挖矿',
      'staking': '质押',
      'yield': '收益',
      'liquidity': '流动性',
      'smart contract': '智能合约',
      'dao': 'DAO',
      'dex': 'DEX',
      'cex': 'CEX'
    };

    // Check for keywords and add corresponding tags
    [cryptoMap, marketMap, techMap].forEach(map => {
      Object.entries(map).forEach(([keyword, tag]) => {
        if (text.includes(keyword)) {
          tags.add(tag);
        }
      });
    });

    // Limit to 10 tags maximum
    return Array.from(tags).slice(0, 10);
  }

  /**
   * Generate SEO keywords
   * @param {string} originalText - Original tweet text
   * @param {string} translatedContent - Chinese translation
   * @param {Array<string>} tags - Generated tags
   * @returns {Array<string>} Array of keywords
   */
  generateKeywords(originalText, translatedContent, tags) {
    const keywords = new Set();
    
    // Add tags as keywords
    tags.forEach(tag => keywords.add(tag));
    
    // Add common crypto keywords
    keywords.add('加密货币分析');
    keywords.add('区块链新闻');
    keywords.add('数字货币');
    keywords.add('投资分析');
    keywords.add('市场动态');

    return Array.from(keywords).slice(0, 15);
  }

  /**
   * Generate descriptive filename with date and topic information
   * @param {string} title - Article title
   * @param {string} date - Article date
   * @returns {string} Generated filename
   */
  generateFilename(title, date) {
    const dateStr = new Date(date).toISOString().split('T')[0].replace(/-/g, '');
    const slug = slugify(title, {
      lower: true,
      strict: true,
      locale: 'zh'
    });
    
    // Limit slug length and add crypto prefix
    const shortSlug = slug.substring(0, 50);
    return `crypto-twitter-${shortSlug}-${dateStr}.md`;
  }

  /**
   * Format the complete article with front matter and content
   * @param {Object} metadata - Article metadata
   * @param {string} content - Article content
   * @returns {string} Complete formatted article
   */
  formatFullArticle(metadata, content) {
    // Format front matter
    const frontMatter = `+++
date = '${metadata.date}'
draft = ${metadata.draft}
title = '${metadata.title.replace(/'/g, "''")}'
description = '${metadata.description.replace(/'/g, "''")}'
tags = [${metadata.tags.map(tag => `'${tag.replace(/'/g, "''")}'`).join(', ')}]
categories = [${metadata.categories.map(cat => `'${cat.replace(/'/g, "''")}'`).join(', ')}]
keywords = [${metadata.keywords.map(kw => `'${kw.replace(/'/g, "''")}'`).join(', ')}]
+++`;

    return `${frontMatter}\n${content}`;
  }
}

export default ArticleGenerator;