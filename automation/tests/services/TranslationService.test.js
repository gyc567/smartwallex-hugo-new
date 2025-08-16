import TranslationService from '../../src/services/TranslationService.js';

describe('TranslationService', () => {
  let translationService;

  beforeEach(() => {
    translationService = new TranslationService({
      primaryService: 'mock-fail', // Force fallback for testing
      fallbackEnabled: true
    });
  });

  describe('constructor', () => {
    test('should initialize with default configuration', () => {
      const service = new TranslationService();
      expect(service.config.primaryService).toBe('local');
      expect(service.config.targetLanguage).toBe('zh-CN');
      expect(service.config.fallbackEnabled).toBe(true);
    });

    test('should accept custom configuration', () => {
      const customConfig = {
        primaryService: 'google',
        targetLanguage: 'zh-TW',
        fallbackEnabled: false
      };
      const service = new TranslationService(customConfig);
      expect(service.config.primaryService).toBe('google');
      expect(service.config.targetLanguage).toBe('zh-TW');
      expect(service.config.fallbackEnabled).toBe(false);
    });

    test('should have crypto terminology dictionary', () => {
      expect(translationService.cryptoTerminology).toBeDefined();
      expect(translationService.cryptoTerminology.bitcoin).toBe('比特币');
      expect(translationService.cryptoTerminology.ethereum).toBe('以太坊');
      expect(translationService.cryptoTerminology.blockchain).toBe('区块链');
    });
  });

  describe('translateText', () => {
    test('should translate crypto terminology correctly', async () => {
      const text = 'Bitcoin and Ethereum are leading cryptocurrencies in the blockchain space';
      const result = await translationService.translateText(text);
      
      expect(result).toContain('比特币');
      expect(result).toContain('以太坊');
      expect(result).toContain('加密货币');
      expect(result).toContain('区块链');
    });

    test('should translate common crypto phrases', async () => {
      const text = 'Breaking news about DeFi and NFT market update';
      const result = await translationService.translateText(text);
      
      expect(result).toContain('突发新闻');
      expect(result).toContain('去中心化金融');
      expect(result).toContain('非同质化代币');
      expect(result).toContain('市场更新');
    });

    test('should handle empty or invalid input', async () => {
      await expect(translationService.translateText('')).rejects.toThrow('Invalid text input for translation');
      await expect(translationService.translateText(null)).rejects.toThrow('Invalid text input for translation');
      await expect(translationService.translateText(123)).rejects.toThrow('Invalid text input for translation');
    });

    test('should return original text when all translation methods fail', async () => {
      const service = new TranslationService({
        primaryService: 'mock-fail',
        fallbackEnabled: false
      });
      
      const text = 'Some random text without crypto terms';
      const result = await service.translateText(text);
      expect(result).toBe(text);
    });

    test('should handle case-insensitive crypto terms', async () => {
      const text = 'BITCOIN and ethereum are CRYPTOCURRENCY assets';
      const result = await translationService.translateText(text);
      
      expect(result).toContain('比特币');
      expect(result).toContain('以太坊');
      expect(result).toContain('加密货币');
    });
  });

  describe('enhanceContent', () => {
    const mockTweetData = {
      text: 'Bitcoin is going to the moon! #crypto #bullish',
      author: { username: 'cryptoexpert' },
      metrics: { retweetCount: 150, likeCount: 500 },
      createdAt: '2025-08-14T09:00:00Z'
    };

    test('should enhance content with market analysis', async () => {
      const translatedContent = '比特币将要冲向月球！#加密货币 #看涨';
      const result = await translationService.enhanceContent(mockTweetData, translatedContent);
      
      expect(result).toContain(translatedContent);
      expect(result).toContain('市场背景分析');
      expect(result).toContain('技术要点解读');
      expect(result).toContain('投资者观点');
      expect(result).toContain('相关影响');
      expect(result).toContain('@cryptoexpert');
      expect(result).toContain('150 次转发');
      expect(result).toContain('500 次点赞');
    });

    test('should include investment disclaimer', async () => {
      const translatedContent = '以太坊价格分析';
      const result = await translationService.enhanceContent(mockTweetData, translatedContent);
      
      expect(result).toContain('本文内容仅供参考，不构成投资建议');
      expect(result).toContain('加密货币投资存在风险，请谨慎决策');
    });

    test('should handle invalid input', async () => {
      await expect(translationService.enhanceContent(null, 'content')).rejects.toThrow('Invalid input for content enhancement');
      await expect(translationService.enhanceContent(mockTweetData, null)).rejects.toThrow('Invalid input for content enhancement');
    });

    test('should generate different investor perspectives based on engagement', async () => {
      const highEngagementTweet = {
        ...mockTweetData,
        metrics: { retweetCount: 1500, likeCount: 3000 }
      };
      
      const result = await translationService.enhanceContent(highEngagementTweet, '测试内容');
      expect(result).toContain('高度关注');
      expect(result).toContain('广泛讨论');
    });
  });

  describe('generateTitle', () => {
    test('should generate engaging Chinese titles', () => {
      const content = '比特币价格突破新高，市场情绪乐观';
      const tweetData = { metrics: { retweetCount: 200 } };
      
      const title = translationService.generateTitle(content, tweetData);
      
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
      expect(title.length).toBeLessThanOrEqual(60);
    });

    test('should include engagement indicators', () => {
      const content = '以太坊技术更新';
      const highEngagementData = { metrics: { retweetCount: 1200 } };
      
      const title = translationService.generateTitle(content, highEngagementData);
      expect(title).toContain('引发热烈讨论');
    });

    test('should handle content without tweet data', () => {
      const content = '区块链技术发展趋势分析';
      const title = translationService.generateTitle(content);
      
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
    });

    test('should throw error for empty content', () => {
      expect(() => translationService.generateTitle('')).toThrow('Content is required for title generation');
      expect(() => translationService.generateTitle(null)).toThrow('Content is required for title generation');
    });

    test('should truncate long titles', () => {
      const longContent = '这是一个非常长的内容标题，包含了很多关于加密货币和区块链技术的详细信息，应该被适当截断以保持可读性';
      const title = translationService.generateTitle(longContent);
      
      expect(title.length).toBeLessThanOrEqual(60);
      if (title.length === 60) {
        expect(title.endsWith('...')).toBe(true);
      }
    });
  });

  describe('private methods', () => {
    test('_extractKeyTopics should identify crypto topics', () => {
      const content = '比特币和以太坊是主要的加密货币';
      const topics = translationService._extractKeyTopics(content);
      
      expect(topics).toContain('比特币');
      expect(topics).toContain('以太坊');
      expect(topics).toContain('加密货币');
    });

    test('_getEngagementIndicator should return appropriate indicators', () => {
      expect(translationService._getEngagementIndicator(1500)).toBe('引发热烈讨论');
      expect(translationService._getEngagementIndicator(750)).toBe('获得广泛关注');
      expect(translationService._getEngagementIndicator(150)).toBe('社区积极响应');
      expect(translationService._getEngagementIndicator(50)).toBe('值得关注');
    });

    test('_optimizeTitleLength should handle long titles', () => {
      const longTitle = '这是一个超过六十个字符限制的非常长的标题，需要被截断处理以确保在界面中正常显示';
      const optimized = translationService._optimizeTitleLength(longTitle);
      
      expect(optimized.length).toBeLessThanOrEqual(60);
      if (longTitle.length > 60) {
        expect(optimized.endsWith('...')).toBe(true);
      }
    });

    test('_optimizeTitleLength should not modify short titles', () => {
      const shortTitle = '短标题';
      const optimized = translationService._optimizeTitleLength(shortTitle);
      
      expect(optimized).toBe(shortTitle);
    });

    test('_enhanceWithTerminology should replace crypto terms', () => {
      const text = 'Bitcoin and ethereum are popular';
      const enhanced = translationService._enhanceWithTerminology(text);
      
      expect(enhanced).toContain('比特币');
      expect(enhanced).toContain('以太坊');
    });

    test('_generateTechnicalAnalysis should provide relevant analysis', () => {
      const priceText = 'Bitcoin price is $50000 with strong support';
      const translatedText = '比特币价格为50000美元，具有强劲支撑';
      const analysis = translationService._generateTechnicalAnalysis(priceText, translatedText);
      
      expect(analysis).toContain('技术分析');
      expect(analysis).toContain('价格');
    });

    test('_generateInvestorPerspective should vary by engagement', () => {
      const highEngagement = { retweetCount: 800, likeCount: 400 }; // Total: 1200 > 1000
      const mediumEngagement = { retweetCount: 30, likeCount: 40 }; // Total: 70 > 50
      const lowEngagement = { retweetCount: 5, likeCount: 10 }; // Total: 15 < 50
      
      const highPerspective = translationService._generateInvestorPerspective(highEngagement);
      const mediumPerspective = translationService._generateInvestorPerspective(mediumEngagement);
      const lowPerspective = translationService._generateInvestorPerspective(lowEngagement);
      
      expect(highPerspective).toContain('高度关注');
      expect(mediumPerspective).toContain('适度关注');
      expect(lowPerspective).toContain('新兴观点');
    });
  });

  describe('error handling', () => {
    test('should handle primary service failures gracefully', async () => {
      const service = new TranslationService({
        primaryService: 'mock-fail',
        fallbackEnabled: true
      });
      
      const text = 'Bitcoin is rising';
      const result = await service.translateText(text);
      
      // Should fallback to local translation
      expect(result).toContain('比特币');
    });

    test('should return original text when all methods fail', async () => {
      const service = new TranslationService({
        primaryService: 'mock-fail',
        fallbackEnabled: false
      });
      
      const text = 'Random text without crypto terms';
      const result = await service.translateText(text);
      
      expect(result).toBe(text);
    });
  });

  describe('integration scenarios', () => {
    test('should handle complete workflow for crypto tweet', async () => {
      const tweetData = {
        text: 'Bitcoin breaks $60k resistance! Bull market confirmed. #crypto #bullish',
        author: { username: 'cryptoanalyst' },
        metrics: { retweetCount: 500, likeCount: 1200 },
        createdAt: '2025-08-14T10:00:00Z'
      };

      // Translate content
      const translated = await translationService.translateText(tweetData.text);
      expect(translated).toContain('比特币');

      // Enhance content
      const enhanced = await translationService.enhanceContent(tweetData, translated);
      expect(enhanced).toContain('市场背景分析');

      // Generate title
      const title = translationService.generateTitle(enhanced, tweetData);
      expect(title).toBeTruthy();
      expect(title.length).toBeLessThanOrEqual(60);
    });

    test('should maintain consistency across multiple calls', async () => {
      const text = 'Ethereum DeFi ecosystem is growing rapidly';
      
      const result1 = await translationService.translateText(text);
      const result2 = await translationService.translateText(text);
      
      expect(result1).toBe(result2);
    });
  });
});