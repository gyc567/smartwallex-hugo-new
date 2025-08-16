
/**
 * TranslationService - Handles English to Chinese translation and content enhancement
 * Provides fallback translation strategies and crypto terminology support
 */
class TranslationService {
  constructor(config = {}) {
    this.config = {
      primaryService: config.primaryService || 'local',
      targetLanguage: config.targetLanguage || 'zh-CN',
      fallbackEnabled: config.fallbackEnabled !== false,
      ...config
    };

    // Crypto terminology dictionary for accurate technical translations
    this.cryptoTerminology = {
      'bitcoin': '比特币',
      'ethereum': '以太坊',
      'blockchain': '区块链',
      'cryptocurrency': '加密货币',
      'cryptocurrencies': '加密货币',
      'crypto': '加密货币',
      'defi': '去中心化金融',
      'nft': '非同质化代币',
      'web3': 'Web3',
      'altcoin': '山寨币',
      'hodl': '长期持有',
      'mining': '挖矿',
      'wallet': '钱包',
      'exchange': '交易所',
      'trading': '交易',
      'bull market': '牛市',
      'bear market': '熊市',
      'pump': '拉升',
      'dump': '抛售',
      'whale': '巨鲸',
      'satoshi': '聪',
      'hash': '哈希',
      'node': '节点',
      'consensus': '共识',
      'smart contract': '智能合约',
      'gas fee': '燃料费',
      'staking': '质押',
      'yield farming': '流动性挖矿',
      'liquidity': '流动性',
      'market cap': '市值',
      'volume': '交易量',
      'volatility': '波动性'
    };

    // Common English to Chinese phrase translations
    this.commonPhrases = {
      'breaking news': '突发新闻',
      'market update': '市场更新',
      'price analysis': '价格分析',
      'technical analysis': '技术分析',
      'fundamental analysis': '基本面分析',
      'investment advice': '投资建议',
      'risk management': '风险管理',
      'portfolio': '投资组合',
      'bullish': '看涨',
      'bearish': '看跌',
      'to the moon': '冲向月球',
      'diamond hands': '钻石手',
      'paper hands': '纸手'
    };
  }

  /**
   * Translate text from English to Chinese with fallback strategies
   * @param {string} text - Text to translate
   * @param {string} targetLang - Target language (default: zh-CN)
   * @returns {Promise<string>} Translated text
   */
  async translateText(text, targetLang = this.config.targetLanguage) {
    if (!text || typeof text !== 'string') {
      throw new Error('Invalid text input for translation');
    }

    try {
      // Primary translation strategy
      const primaryResult = await this._translateWithPrimaryService(text, targetLang);
      if (primaryResult) {
        return this._enhanceWithTerminology(primaryResult);
      }
    } catch (error) {
      console.warn('Primary translation service failed:', error.message);
    }

    // Fallback to local dictionary translation
    if (this.config.fallbackEnabled) {
      try {
        const fallbackResult = await this._translateWithFallback(text);
        return this._enhanceWithTerminology(fallbackResult);
      } catch (error) {
        console.warn('Fallback translation failed:', error.message);
      }
    }

    // Last resort: return original text with warning
    console.warn('All translation methods failed, returning original text');
    return text;
  }

  /**
   * Enhance tweet content into comprehensive articles
   * @param {Object} tweetData - Original tweet data
   * @param {string} translatedContent - Translated tweet content
   * @returns {Promise<string>} Enhanced article content
   */
  async enhanceContent(tweetData, translatedContent) {
    if (!tweetData || !translatedContent) {
      throw new Error('Invalid input for content enhancement');
    }

    const { text, author, metrics, createdAt } = tweetData;

    // Generate enhanced content with context and analysis
    const enhancedContent = `${translatedContent}

## 市场背景分析

这条推文反映了当前加密货币市场的重要动态。作为来自 @${author.username} 的观点，该内容在社区中获得了 ${metrics.retweetCount} 次转发和 ${metrics.likeCount} 次点赞，显示了较高的关注度。

## 技术要点解读

${this._generateTechnicalAnalysis(text, translatedContent)}

## 投资者观点

${this._generateInvestorPerspective(metrics)}

## 相关影响

这一观点可能对以下方面产生影响：
- 市场情绪和投资者信心
- 相关加密货币价格走势
- 行业发展趋势和政策导向

*本文内容仅供参考，不构成投资建议。加密货币投资存在风险，请谨慎决策。*`;

    return enhancedContent;
  }

  /**
   * Generate engaging Chinese titles for articles
   * @param {string} content - Article content
   * @param {Object} tweetData - Original tweet data
   * @returns {string} Generated Chinese title
   */
  generateTitle(content, tweetData = {}) {
    if (!content) {
      throw new Error('Content is required for title generation');
    }

    const { metrics = {} } = tweetData;
    const retweetCount = metrics.retweetCount || 0;

    // Extract key topics from content
    const topics = this._extractKeyTopics(content);
    const mainTopic = topics[0] || '加密货币';

    // Generate title based on engagement and content
    const engagementIndicator = this._getEngagementIndicator(retweetCount);
    const titleTemplates = [
      `${mainTopic}重大消息：${engagementIndicator}`,
      `市场热议：${mainTopic}最新动态分析`,
      `${mainTopic}突破性进展：社区反响强烈`,
      `深度解读：${mainTopic}市场影响分析`,
      `${mainTopic}最新资讯：${engagementIndicator}`
    ];

    // Select title based on engagement level - use first template for high engagement
    const selectedTemplate = retweetCount > 1000 ? titleTemplates[0] : titleTemplates[Math.floor(Math.random() * titleTemplates.length)];

    // Ensure title length is appropriate (20-60 characters)
    return this._optimizeTitleLength(selectedTemplate);
  }

  /**
   * Primary translation service (placeholder for external API)
   * @private
   */
  async _translateWithPrimaryService(text, targetLang) {
    // In a real implementation, this would call Google Translate API, Azure Translator, etc.
    // For now, we'll simulate with a delay and return null to trigger fallback
    await new Promise(resolve => setTimeout(resolve, 100));

    // Simulate API failure to test fallback
    if (this.config.primaryService === 'mock-fail') {
      throw new Error('Mock primary service failure');
    }

    // For testing purposes, return null to trigger fallback
    return null;
  }

  /**
   * Fallback translation using local dictionary
   * @private
   */
  async _translateWithFallback(text) {
    let translatedText = text;

    // Replace crypto terminology
    Object.entries(this.cryptoTerminology).forEach(([english, chinese]) => {
      const regex = new RegExp(`\\b${english}\\b`, 'gi');
      translatedText = translatedText.replace(regex, chinese);
    });

    // Replace common phrases
    Object.entries(this.commonPhrases).forEach(([english, chinese]) => {
      const regex = new RegExp(english, 'gi');
      translatedText = translatedText.replace(regex, chinese);
    });

    // Basic sentence structure translation (simplified)
    translatedText = this._basicSentenceTranslation(translatedText);

    return translatedText;
  }

  /**
   * Enhance translation with crypto terminology
   * @private
   */
  _enhanceWithTerminology(text) {
    let enhancedText = text;

    // Ensure crypto terms are properly translated
    Object.entries(this.cryptoTerminology).forEach(([english, chinese]) => {
      const regex = new RegExp(`\\b${english}\\b`, 'gi');
      enhancedText = enhancedText.replace(regex, chinese);
    });

    return enhancedText;
  }

  /**
   * Generate technical analysis section
   * @private
   */
  _generateTechnicalAnalysis(originalText, translatedText) {
    const hasPrice = /price|价格|\$|USD/i.test(originalText);
    const hasTechnical = /chart|图表|support|resistance|支撑|阻力/i.test(originalText);

    if (hasPrice && hasTechnical) {
      return '从技术分析角度来看，该观点涉及价格走势和关键技术指标，值得投资者密切关注相关图表形态和支撑阻力位。';
    } else if (hasPrice) {
      return '该内容涉及价格相关信息，建议结合当前市场环境和历史数据进行综合分析。';
    } else {
      return '从技术层面分析，该观点反映了行业发展的重要趋势，可能对未来市场格局产生深远影响。';
    }
  }

  /**
   * Generate investor perspective section
   * @private
   */
  _generateInvestorPerspective(metrics) {
    const { retweetCount = 0, likeCount = 0 } = metrics;
    const totalEngagement = retweetCount + likeCount;

    if (totalEngagement > 1000) {
      return '高度关注：该观点在投资者社区中引起了广泛讨论，反映了市场对此话题的高度关注。投资者应当谨慎评估其对投资决策的潜在影响。';
    } else if (totalEngagement > 50) {
      return '适度关注：该观点获得了一定程度的社区认可，值得投资者关注并结合自身投资策略进行考量。';
    } else {
      return '新兴观点：该观点刚刚出现，投资者可以关注其后续发展和市场反应，但应保持谨慎态度。';
    }
  }

  /**
   * Extract key topics from content
   * @private
   */
  _extractKeyTopics(content) {
    const topics = [];

    // Check for crypto terminology
    Object.entries(this.cryptoTerminology).forEach(([english, chinese]) => {
      if (content.toLowerCase().includes(english.toLowerCase()) || content.includes(chinese)) {
        topics.push(chinese);
      }
    });

    // Default topics if none found
    if (topics.length === 0) {
      topics.push('加密货币', '区块链', '数字资产');
    }

    return [...new Set(topics)]; // Remove duplicates
  }

  /**
   * Get engagement indicator based on retweet count
   * @private
   */
  _getEngagementIndicator(retweetCount) {
    if (retweetCount > 1000) return '引发热烈讨论';
    if (retweetCount > 500) return '获得广泛关注';
    if (retweetCount > 100) return '社区积极响应';
    return '值得关注';
  }

  /**
   * Optimize title length for readability
   * @private
   */
  _optimizeTitleLength(title) {
    if (title.length <= 60) return title;

    // Truncate and add ellipsis if too long
    return title.substring(0, 57) + '...';
  }

  /**
   * Basic sentence structure translation (simplified implementation)
   * @private
   */
  _basicSentenceTranslation(text) {
    // This is a very basic implementation
    // In a real scenario, this would use more sophisticated NLP

    // Common English patterns to Chinese
    const patterns = [
      { pattern: /\bis\s+going\s+to\b/gi, replacement: '将要' },
      { pattern: /\bwill\s+be\b/gi, replacement: '将会是' },
      { pattern: /\bthis\s+is\b/gi, replacement: '这是' },
      { pattern: /\bthat\s+is\b/gi, replacement: '那是' },
      { pattern: /\bwe\s+are\b/gi, replacement: '我们是' },
      { pattern: /\bthey\s+are\b/gi, replacement: '他们是' },
      { pattern: /\bI\s+think\b/gi, replacement: '我认为' },
      { pattern: /\bI\s+believe\b/gi, replacement: '我相信' }
    ];

    let translatedText = text;
    patterns.forEach(({ pattern, replacement }) => {
      translatedText = translatedText.replace(pattern, replacement);
    });

    return translatedText;
  }
}

export default TranslationService;